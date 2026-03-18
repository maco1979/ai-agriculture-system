/**
 * PTZ云台摄像头控制组件
 * 支持真实的云台转动、变焦、对焦等物理操作
 * 修复：连接状态正确同步；接入真实 ptz/action + ptz/move 路由；新增自动跟踪开关
 */

import React, { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface PTZPosition {
  pan: number;
  tilt: number;
  zoom: number;
}

interface PTZStatus {
  connected: boolean;
  protocol?: string;
  connection_type?: string;
  position?: PTZPosition;
  presets?: Record<number, any>;
  auto_tracking?: boolean;
  simulated?: boolean;
}

interface TrackStatus {
  running: boolean;
  target_found: boolean;
  target_bbox: number[] | null;   // [x, y, w, h]
  frame_size: number[] | null;     // [w, h]
  pan_offset: number;
  tilt_offset: number;
  last_adjust: string | null;
  tracker_type: string;
  mode: 'real' | 'simulated';
  error: string | null;
  position?: PTZPosition;
}

interface PTZControlProps {
  apiClient: any;
}

export const PTZControl: React.FC<PTZControlProps> = ({ apiClient }) => {
  const [ptzStatus, setPtzStatus] = useState<PTZStatus>({ connected: false });
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [successMsg, setSuccessMsg] = useState<string>('');
  const [autoTracking, setAutoTracking] = useState(false);
  const [trackStatus, setTrackStatus] = useState<TrackStatus | null>(null);
  const trackPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const posPollRef   = useRef<ReturnType<typeof setInterval> | null>(null); // 位置定时刷新

  // 连接配置
  const [protocol, setProtocol] = useState('pelco_d');
  const [connectionType, setConnectionType] = useState('serial');
  const [serialPort, setSerialPort] = useState('COM3');
  const [baudrate, setBaudrate] = useState(9600);
  const [networkHost, setNetworkHost] = useState('192.168.1.100');
  const [networkPort, setNetworkPort] = useState(5000);
  const [httpUrl, setHttpUrl] = useState('http://192.168.1.100');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin');

  // 控制参数
  const [speed, setSpeed] = useState(50);
  const [presetId, setPresetId] = useState(1);
  const [presetName, setPresetName] = useState('');

  // 位置控制
  const [targetPan, setTargetPan] = useState(0);
  const [targetTilt, setTargetTilt] = useState(0);
  const [targetZoom, setTargetZoom] = useState(1.0);

  // 当前显示位置（从后端同步）
  const [position, setPosition] = useState<PTZPosition>({ pan: 0, tilt: 0, zoom: 1.0 });

  // 长按方向键计时器
  const pressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pressInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // 加载PTZ状态 + 启动位置定时刷新
  useEffect(() => {
    checkPTZStatus();

    // 1秒刷新一次位置（即使没有开启跟踪也保持同步）
    posPollRef.current = setInterval(async () => {
      try {
        const res = await apiClient.get('/api/camera/ptz/status');
        if (res.success && res.data?.position) {
          setPosition(res.data.position);
          if (typeof res.data.auto_tracking === 'boolean') {
            setAutoTracking(res.data.auto_tracking);
          }
        }
      } catch {}
    }, 1000);

    return () => {
      // 清除所有轮询
      if (trackPollRef.current) clearInterval(trackPollRef.current);
      if (posPollRef.current)   clearInterval(posPollRef.current);
    };
  }, []);

  // 提示信息自动清除
  useEffect(() => {
    if (successMsg) {
      const t = setTimeout(() => setSuccessMsg(''), 2000);
      return () => clearTimeout(t);
    }
  }, [successMsg]);

  const checkPTZStatus = async () => {
    try {
      const res = await apiClient.get('/api/camera/ptz/status');
      if (res.success && res.data) {
        const data: PTZStatus = res.data;
        setPtzStatus(data);
        if (data.position) setPosition(data.position);
        if (typeof data.auto_tracking === 'boolean') setAutoTracking(data.auto_tracking);
      }
    } catch (err) {
      console.error('获取PTZ状态失败:', err);
    }
  };

  // 清除长按计时器
  const clearPressTimers = () => {
    if (pressTimer.current) { clearTimeout(pressTimer.current); pressTimer.current = null; }
    if (pressInterval.current) { clearInterval(pressInterval.current); pressInterval.current = null; }
  };

  // 连接PTZ
  const connectPTZ = async () => {
    setLoading(true);
    setError('');

    try {
      const params: any = {
        protocol,
        connection_type: connectionType,
      };

      if (connectionType === 'serial') {
        params.port = serialPort;
        params.baudrate = baudrate;
        params.address = 1;
      } else if (connectionType === 'network') {
        params.host = networkHost;
        params.network_port = networkPort;
        params.address = 1;
      } else if (connectionType === 'http') {
        params.base_url = httpUrl;
        params.username = username;
        params.password = password;
      }

      const res = await apiClient.post('/api/camera/ptz/connect', params);

      if (res.success) {
        setError('');
        setSuccessMsg(res.data?.message || '云台已连接');
        await checkPTZStatus();
      } else {
        setError(res.data?.message || res.message || '连接失败');
      }
    } catch (err: any) {
      setError(err.message || '连接失败');
    } finally {
      setLoading(false);
    }
  };

  // 断开PTZ
  const disconnectPTZ = async () => {
    setLoading(true);
    try {
      if (autoTracking) {
        await apiClient.post('/api/camera/ptz/auto-track/stop');
        setAutoTracking(false);
      }
      const res = await apiClient.post('/api/camera/ptz/disconnect');
      if (res.success) {
        setPtzStatus({ connected: false });
        setPosition({ pan: 0, tilt: 0, zoom: 1.0 });
        setError('');
      }
    } catch (err: any) {
      setError(err.message || '断开失败');
    } finally {
      setLoading(false);
    }
  };

  // 执行PTZ动作（单次）
  const executeAction = async (action: string) => {
    if (!ptzStatus.connected) {
      setError('请先连接PTZ云台');
      return;
    }
    setActionLoading(true);
    try {
      const extra: any = { action, speed };
      if (action === 'preset_set' || action === 'preset_goto') {
        extra.preset_id = presetId;
      }
      const res = await apiClient.post('/api/camera/ptz/action', extra);
      if (res.success) {
        setError('');
        if (res.data?.position) setPosition(res.data.position);
      } else {
        setError(res.data?.message || '操作失败');
      }
    } catch (err: any) {
      setError(err.message || '操作失败');
    } finally {
      setActionLoading(false);
    }
  };

  // 长按支持：按下开始移动，松开发停止
  const handleDirectionMouseDown = (action: string) => {
    executeAction(action);
    pressTimer.current = setTimeout(() => {
      pressInterval.current = setInterval(() => {
        executeAction(action);
      }, 300);
    }, 500);
  };

  const handleDirectionMouseUp = () => {
    clearPressTimers();
    executeAction('stop');
  };

  // 移动到绝对位置
  const moveToPosition = async () => {
    if (!ptzStatus.connected) {
      setError('请先连接PTZ云台');
      return;
    }
    setLoading(true);
    try {
      const res = await apiClient.post('/api/camera/ptz/move', {
        pan: targetPan,
        tilt: targetTilt,
        zoom: targetZoom,
        speed,
      });
      if (res.success) {
        setError('');
        setSuccessMsg('移动完成');
        await checkPTZStatus();
      } else {
        setError(res.data?.message || '移动失败');
      }
    } catch (err: any) {
      setError(err.message || '移动失败');
    } finally {
      setLoading(false);
    }
  };

  // 设置预置位
  const setPreset = async () => {
    if (!ptzStatus.connected) { setError('请先连接PTZ云台'); return; }
    try {
      const res = await apiClient.post('/api/camera/ptz/preset/set', {
        preset_id: presetId,
        name: presetName || `预置位${presetId}`,
      });
      if (res.success) { setError(''); setSuccessMsg(`预置位${presetId}已保存`); await checkPTZStatus(); }
      else { setError(res.data?.message || '设置失败'); }
    } catch (err: any) { setError(err.message || '设置失败'); }
  };

  // 转到预置位
  const gotoPreset = async () => {
    if (!ptzStatus.connected) { setError('请先连接PTZ云台'); return; }
    try {
      const res = await apiClient.post('/api/camera/ptz/preset/goto', { preset_id: presetId });
      if (res.success) { setError(''); setSuccessMsg(`已跳转预置位${presetId}`); await checkPTZStatus(); }
      else { setError(res.data?.message || '跳转失败'); }
    } catch (err: any) { setError(err.message || '跳转失败'); }
  };

  // 切换自动跟踪
  const toggleAutoTracking = async () => {
    if (!ptzStatus.connected) { setError('请先连接PTZ云台'); return; }
    try {
      if (autoTracking) {
        const res = await apiClient.post('/api/camera/ptz/auto-track/stop');
        if (res.success) {
          setAutoTracking(false);
          setSuccessMsg('自动跟踪已停止');
          // 停止轮询
          if (trackPollRef.current) {
            clearInterval(trackPollRef.current);
            trackPollRef.current = null;
          }
          setTrackStatus(null);
        } else { setError(res.data?.message || '停止失败'); }
      } else {
        const res = await apiClient.post('/api/camera/ptz/auto-track/start');
        if (res.success) {
          setAutoTracking(true);
          setSuccessMsg(`自动跟踪已启动（${res.data?.mode === 'real' ? '真实摄像头' : '模拟'}模式）`);
          // 启动轮询（500ms 一次）
          if (trackPollRef.current) clearInterval(trackPollRef.current);
          trackPollRef.current = setInterval(async () => {
            try {
              const ts = await apiClient.get('/api/camera/ptz/auto-track/status');
              if (ts.success && ts.data) {
                setTrackStatus(ts.data);
                if (ts.data.position) setPosition(ts.data.position);
                // 后端标记停止时同步前端状态
                if (!ts.data.auto_tracking) {
                  setAutoTracking(false);
                  if (trackPollRef.current) {
                    clearInterval(trackPollRef.current);
                    trackPollRef.current = null;
                  }
                }
              }
            } catch {}
          }, 500);
        } else { setError(res.data?.message || '启动失败，请先开启摄像头'); }
      }
    } catch (err: any) { setError(err.message || '操作失败'); }
  };

  // 方向按钮通用样式
  const dirBtnCls = cn(
    'px-5 py-3 rounded-lg font-bold text-sm transition-all select-none',
    'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30',
    'hover:bg-cyber-cyan/40 active:scale-95',
    (actionLoading || !ptzStatus.connected) && 'opacity-40 cursor-not-allowed pointer-events-none',
  );

  return (
    <div className="space-y-4">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-cyber-cyan">PTZ云台控制</h3>
        <div className="flex items-center gap-2">
          {ptzStatus.simulated && (
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
              模拟
            </span>
          )}
          <div className={cn(
            'px-3 py-1 rounded-lg text-xs font-bold',
            ptzStatus.connected
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'bg-gray-700/50 text-gray-400 border border-gray-600/30',
          )}>
            {ptzStatus.connected ? '已连接' : '未连接'}
          </div>
        </div>
      </div>

      {/* 成功提示 */}
      {successMsg && (
        <div className="p-2 rounded-lg bg-green-500/10 border border-green-500/30">
          <p className="text-xs text-green-400">{successMsg}</p>
        </div>
      )}

      {/* 连接配置（未连接时显示） */}
      {!ptzStatus.connected && (
        <div className="space-y-3 p-4 rounded-xl bg-white/5 border border-white/10">
          <h4 className="text-sm font-bold text-gray-300">连接配置</h4>

          {/* 协议选择 */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">控制协议</label>
            <select
              value={protocol}
              onChange={(e) => setProtocol(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
            >
              <option value="pelco_d">Pelco-D（最常用）</option>
              <option value="pelco_p">Pelco-P</option>
              <option value="visca">VISCA（Sony）</option>
              <option value="onvif">ONVIF</option>
              <option value="http">HTTP API</option>
            </select>
          </div>

          {/* 连接类型 */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">连接类型</label>
            <select
              value={connectionType}
              onChange={(e) => setConnectionType(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
            >
              <option value="serial">串口（RS-485/RS-232）</option>
              <option value="network">网络（TCP/IP）</option>
              <option value="http">HTTP接口</option>
            </select>
          </div>

          {/* 串口配置 */}
          {connectionType === 'serial' && (
            <>
              <div>
                <label className="text-xs text-gray-400 block mb-1">串口（Windows: COM3，Linux: /dev/ttyUSB0）</label>
                <input
                  type="text"
                  value={serialPort}
                  onChange={(e) => setSerialPort(e.target.value)}
                  placeholder="COM3 或 /dev/ttyUSB0"
                  className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">波特率</label>
                <select
                  value={baudrate}
                  onChange={(e) => setBaudrate(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                >
                  <option value={2400}>2400</option>
                  <option value={4800}>4800</option>
                  <option value={9600}>9600</option>
                  <option value={19200}>19200</option>
                  <option value={38400}>38400</option>
                </select>
              </div>
            </>
          )}

          {/* 网络配置 */}
          {connectionType === 'network' && (
            <>
              <div>
                <label className="text-xs text-gray-400 block mb-1">IP地址</label>
                <input
                  type="text"
                  value={networkHost}
                  onChange={(e) => setNetworkHost(e.target.value)}
                  placeholder="192.168.1.100"
                  className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">端口</label>
                <input
                  type="number"
                  value={networkPort}
                  onChange={(e) => setNetworkPort(Number(e.target.value))}
                  placeholder="5000"
                  className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                />
              </div>
            </>
          )}

          {/* HTTP配置 */}
          {connectionType === 'http' && (
            <>
              <div>
                <label className="text-xs text-gray-400 block mb-1">URL地址</label>
                <input
                  type="text"
                  value={httpUrl}
                  onChange={(e) => setHttpUrl(e.target.value)}
                  placeholder="http://192.168.1.100"
                  className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">用户名</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="admin"
                    className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">密码</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="admin"
                    className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                  />
                </div>
              </div>
            </>
          )}

          <button
            onClick={connectPTZ}
            disabled={loading}
            className={cn(
              'w-full px-4 py-2 rounded-lg font-bold text-sm transition-all',
              'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30',
              'hover:bg-cyber-cyan/30 hover:border-cyber-cyan/50',
              loading && 'opacity-50 cursor-not-allowed',
            )}
          >
            {loading ? '连接中...' : '连接PTZ云台'}
          </button>
        </div>
      )}

      {/* PTZ控制面板（已连接时显示） */}
      {ptzStatus.connected && (
        <>
          {/* 当前位置 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-bold text-gray-300">当前位置</h4>
              <button
                onClick={checkPTZStatus}
                className="text-[10px] text-gray-500 hover:text-cyber-cyan transition-colors"
              >
                刷新
              </button>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center">
                <div className="text-[10px] text-gray-400 mb-1">水平 Pan</div>
                <div className="text-lg font-bold text-cyber-cyan">{position.pan.toFixed(1)}°</div>
              </div>
              <div className="text-center">
                <div className="text-[10px] text-gray-400 mb-1">垂直 Tilt</div>
                <div className="text-lg font-bold text-cyber-cyan">{position.tilt.toFixed(1)}°</div>
              </div>
              <div className="text-center">
                <div className="text-[10px] text-gray-400 mb-1">变焦 Zoom</div>
                <div className="text-lg font-bold text-cyber-cyan">{position.zoom.toFixed(1)}x</div>
              </div>
            </div>
          </div>

          {/* 方向控制（支持长按） */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <h4 className="text-sm font-bold text-gray-300 mb-3">方向控制</h4>
            <div className="flex flex-col items-center space-y-2">
              {/* 上 */}
              <button
                className={dirBtnCls}
                onMouseDown={() => handleDirectionMouseDown('tilt_up')}
                onMouseUp={handleDirectionMouseUp}
                onMouseLeave={handleDirectionMouseUp}
                onTouchStart={() => handleDirectionMouseDown('tilt_up')}
                onTouchEnd={handleDirectionMouseUp}
              >
                ▲ 上仰
              </button>

              {/* 左 停止 右 */}
              <div className="flex items-center space-x-2">
                <button
                  className={dirBtnCls}
                  onMouseDown={() => handleDirectionMouseDown('pan_left')}
                  onMouseUp={handleDirectionMouseUp}
                  onMouseLeave={handleDirectionMouseUp}
                  onTouchStart={() => handleDirectionMouseDown('pan_left')}
                  onTouchEnd={handleDirectionMouseUp}
                >
                  ◄ 左转
                </button>
                <button
                  onClick={() => executeAction('stop')}
                  disabled={actionLoading || !ptzStatus.connected}
                  className="px-5 py-3 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 font-bold text-sm transition-all disabled:opacity-40"
                >
                  停止
                </button>
                <button
                  className={dirBtnCls}
                  onMouseDown={() => handleDirectionMouseDown('pan_right')}
                  onMouseUp={handleDirectionMouseUp}
                  onMouseLeave={handleDirectionMouseUp}
                  onTouchStart={() => handleDirectionMouseDown('pan_right')}
                  onTouchEnd={handleDirectionMouseUp}
                >
                  右转 ►
                </button>
              </div>

              {/* 下 */}
              <button
                className={dirBtnCls}
                onMouseDown={() => handleDirectionMouseDown('tilt_down')}
                onMouseUp={handleDirectionMouseUp}
                onMouseLeave={handleDirectionMouseUp}
                onTouchStart={() => handleDirectionMouseDown('tilt_down')}
                onTouchEnd={handleDirectionMouseUp}
              >
                ▼ 下俯
              </button>
            </div>
          </div>

          {/* 变焦控制 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <h4 className="text-sm font-bold text-gray-300 mb-3">变焦控制</h4>
            <div className="flex items-center justify-center space-x-2">
              <button
                onClick={() => executeAction('zoom_out')}
                disabled={actionLoading || !ptzStatus.connected}
                className="px-6 py-2 rounded-lg bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30 hover:bg-cyber-cyan/30 font-bold disabled:opacity-40"
              >
                拉远 −
              </button>
              <span className="text-sm text-gray-400 w-12 text-center">{position.zoom.toFixed(1)}x</span>
              <button
                onClick={() => executeAction('zoom_in')}
                disabled={actionLoading || !ptzStatus.connected}
                className="px-6 py-2 rounded-lg bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30 hover:bg-cyber-cyan/30 font-bold disabled:opacity-40"
              >
                拉近 +
              </button>
            </div>
          </div>

          {/* 速度控制 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-bold text-gray-300">速度</h4>
              <span className="text-xs text-cyber-cyan font-bold">{speed}</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="w-full accent-cyan-400"
            />
          </div>

          {/* 绝对位置移动 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <h4 className="text-sm font-bold text-gray-300 mb-3">绝对位置移动</h4>
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div>
                <label className="text-[10px] text-gray-400 block mb-1">Pan（水平°）</label>
                <input
                  type="number"
                  value={targetPan}
                  onChange={(e) => setTargetPan(Number(e.target.value))}
                  min="-180" max="180"
                  className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                />
              </div>
              <div>
                <label className="text-[10px] text-gray-400 block mb-1">Tilt（垂直°）</label>
                <input
                  type="number"
                  value={targetTilt}
                  onChange={(e) => setTargetTilt(Number(e.target.value))}
                  min="-90" max="90"
                  className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                />
              </div>
              <div>
                <label className="text-[10px] text-gray-400 block mb-1">Zoom（倍）</label>
                <input
                  type="number"
                  value={targetZoom}
                  onChange={(e) => setTargetZoom(Number(e.target.value))}
                  min="1" max="20" step="0.5"
                  className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                />
              </div>
            </div>
            <button
              onClick={moveToPosition}
              disabled={loading}
              className="w-full px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30 font-bold text-sm disabled:opacity-40"
            >
              {loading ? '移动中...' : '移动到此位置'}
            </button>
          </div>

          {/* 预置位控制 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <h4 className="text-sm font-bold text-gray-300 mb-3">预置位控制</h4>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-gray-400 block mb-1">预置位编号 (1-256)</label>
                  <input
                    type="number"
                    value={presetId}
                    onChange={(e) => setPresetId(Number(e.target.value))}
                    min="1" max="256"
                    className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-gray-400 block mb-1">名称（可选）</label>
                  <input
                    type="text"
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    placeholder="如：大门"
                    className="w-full px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-white text-sm"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={setPreset}
                  className="px-4 py-2 rounded-lg bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30 font-bold text-sm"
                >
                  保存预置位
                </button>
                <button
                  onClick={gotoPreset}
                  className="px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30 font-bold text-sm"
                >
                  跳转预置位
                </button>
              </div>
            </div>
          </div>

          {/* 自动跟踪 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
            {/* 标题行 */}
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-gray-300">AI 自动跟踪</h4>
                <p className="text-[10px] text-gray-500 mt-0.5">
                  摄像头识别目标后自动调整云台方向
                </p>
              </div>
              <button
                onClick={toggleAutoTracking}
                className={cn(
                  'px-4 py-2 rounded-lg font-bold text-sm transition-all border',
                  autoTracking
                    ? 'bg-red-500/20 text-red-400 border-red-500/30 hover:bg-red-500/30'
                    : 'bg-cyber-cyan/20 text-cyber-cyan border-cyber-cyan/30 hover:bg-cyber-cyan/30',
                )}
              >
                {autoTracking ? '停止跟踪' : '启动跟踪'}
              </button>
            </div>

            {/* 运行状态指示 */}
            {autoTracking && trackStatus && (
              <div className="space-y-2">
                {/* 状态行 */}
                <div className="flex items-center gap-3">
                  <div className={cn(
                    'w-2 h-2 rounded-full',
                    trackStatus.running ? 'bg-green-400 animate-pulse' : 'bg-gray-500',
                  )} />
                  <span className={cn(
                    'text-xs font-bold',
                    trackStatus.running ? 'text-green-400' : 'text-gray-400',
                  )}>
                    {trackStatus.running ? '跟踪运行中' : '等待启动'}
                  </span>
                  <span className="text-[10px] text-gray-500 ml-auto">
                    {trackStatus.mode === 'real' ? '🎥 真实摄像头' : '💻 软件模拟'}
                  </span>
                </div>

                {/* 目标检测结果 */}
                <div className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-xs border',
                  trackStatus.target_found
                    ? 'bg-green-500/10 border-green-500/30 text-green-300'
                    : 'bg-gray-700/30 border-gray-600/30 text-gray-400',
                )}>
                  <span className="font-bold">{trackStatus.target_found ? '✓ 目标锁定' : '○ 搜索中'}</span>
                  {trackStatus.target_found && trackStatus.target_bbox && trackStatus.frame_size && (
                    <span className="ml-2 font-mono text-[10px]">
                      [{trackStatus.target_bbox[0]}, {trackStatus.target_bbox[1]},&nbsp;
                       {trackStatus.target_bbox[2]}×{trackStatus.target_bbox[3]}]
                      &nbsp;/&nbsp;{trackStatus.frame_size[0]}×{trackStatus.frame_size[1]}
                    </span>
                  )}
                </div>

                {/* 偏移量 + 云台调整方向 */}
                {trackStatus.target_found && (
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 rounded-lg bg-black/30 border border-white/5">
                      <div className="text-[10px] text-gray-400 mb-1">水平偏移 (Pan)</div>
                      <div className={cn(
                        'text-sm font-bold font-mono',
                        Math.abs(trackStatus.pan_offset) < 5 ? 'text-green-400' : 'text-yellow-400',
                      )}>
                        {trackStatus.pan_offset > 0 ? '►' : trackStatus.pan_offset < 0 ? '◄' : '●'}
                        &nbsp;{trackStatus.pan_offset.toFixed(1)}°
                      </div>
                    </div>
                    <div className="p-2 rounded-lg bg-black/30 border border-white/5">
                      <div className="text-[10px] text-gray-400 mb-1">垂直偏移 (Tilt)</div>
                      <div className={cn(
                        'text-sm font-bold font-mono',
                        Math.abs(trackStatus.tilt_offset) < 5 ? 'text-green-400' : 'text-yellow-400',
                      )}>
                        {trackStatus.tilt_offset > 0 ? '▲' : trackStatus.tilt_offset < 0 ? '▼' : '●'}
                        &nbsp;{trackStatus.tilt_offset.toFixed(1)}°
                      </div>
                    </div>
                  </div>
                )}

                {/* 可视化目标框（简易 Canvas 风格） */}
                {trackStatus.target_found && trackStatus.target_bbox && trackStatus.frame_size && (
                  <div className="relative w-full bg-black/40 border border-white/10 rounded-lg overflow-hidden"
                    style={{ paddingTop: `${(trackStatus.frame_size[1] / trackStatus.frame_size[0]) * 100}%` }}>
                    <div className="absolute inset-0">
                      {/* 中心十字 */}
                      <div className="absolute top-1/2 left-0 right-0 h-px bg-white/10" />
                      <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/10" />
                      {/* 目标框 */}
                      {(() => {
                        const [bx, by, bw, bh] = trackStatus.target_bbox!;
                        const [fw, fh] = trackStatus.frame_size!;
                        return (
                          <div
                            className="absolute border-2 border-green-400 rounded-sm"
                            style={{
                              left: `${(bx / fw) * 100}%`,
                              top: `${(by / fh) * 100}%`,
                              width: `${(bw / fw) * 100}%`,
                              height: `${(bh / fh) * 100}%`,
                            }}
                          >
                            <span className="absolute -top-4 left-0 text-[9px] text-green-400 font-bold bg-black/60 px-1 rounded">
                              TARGET
                            </span>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                )}

                {/* 上次调整时间 */}
                {trackStatus.last_adjust && (
                  <p className="text-[10px] text-gray-500 text-right">
                    上次调整: {new Date(trackStatus.last_adjust).toLocaleTimeString()}
                  </p>
                )}

                {/* 错误提示 */}
                {trackStatus.error && (
                  <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/30">
                    <p className="text-[10px] text-red-400">{trackStatus.error}</p>
                  </div>
                )}
              </div>
            )}

            {/* 等待启动时的提示 */}
            {autoTracking && !trackStatus && (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
                <span className="text-xs text-yellow-400">正在初始化...</span>
              </div>
            )}
          </div>

          {/* 断开连接 */}
          <button
            onClick={disconnectPTZ}
            disabled={loading}
            className="w-full px-4 py-2 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 font-bold text-sm disabled:opacity-40"
          >
            断开连接
          </button>
        </>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}

      {/* 使用说明 */}
      <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
        <p className="text-xs text-yellow-400 font-bold mb-1">📖 PTZ云台控制说明</p>
        <ul className="text-[10px] text-yellow-300/70 space-y-1">
          <li>• 支持真实云台物理转动（串口/网络/HTTP），无硬件时显示"模拟"标签</li>
          <li>• 长按方向键可持续移动，松开自动发送停止指令</li>
          <li>• 自动跟踪：需摄像头已开启，AI识别目标后自动调整云台</li>
          <li>• Windows串口格式：COM3，Linux/Mac格式：/dev/ttyUSB0</li>
          <li>• 支持协议：Pelco-D/P（最常用）、VISCA（Sony）、ONVIF、HTTP</li>
        </ul>
      </div>
    </div>
  );
};
