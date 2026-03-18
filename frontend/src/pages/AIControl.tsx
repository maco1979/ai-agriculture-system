import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Cpu, 
  Shield, 
  Wifi, 
  Mic, 
  MicOff, 
  Power, 
  RefreshCw, 
  Video, 
  Settings,
  Activity,
  Zap,
  CheckCircle,
  Lock,
  ArrowRight,
  Maximize2,
  Minimize2,
  X
} from 'lucide-react';
import { apiClient, Device, JEPAData } from '@/services/api';
import { cn } from '@/lib/utils';
import { BentoCard } from '@/components/ui/BentoCard';
import { DeviceCard } from '@/components/ui/DeviceCard';
import { PTZControl } from '@/components/PTZControl';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

// Mock data to fallback if API fails
const mockPresets = [
  { id: 1, name: '农业智能', description: '自主灌溉和养分监测', devices: [1, 2, 3] },
  { id: 2, name: '生态节能', description: '超低功耗模式', devices: [1, 4] },
  { id: 3, name: '最大安全', description: '全方位生物识别监控', devices: [3, 4] },
];

export function AIControl() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevices, setSelectedDevices] = useState<number[]>([]);
  const [isMasterActive, setIsMasterActive] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(mockPresets[0]);
  
  // JEPA-DT-MPC state
  const [isJepaActive, setIsJepaActive] = useState(false);
  const [jepaData, setJepaData] = useState<JEPAData | null>(null);
  const [jepaModelStatus, setJepaModelStatus] = useState('ready');

  // Voice recognition
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [lastCommand, setLastCommand] = useState('');
  const voiceRecognitionRef = useRef<any>(null);
  
  // Camera state
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [cameraFrame, setCameraFrame] = useState('');
  const [cameraError, setCameraError] = useState('');
  const [cameraSource, setCameraSource] = useState<'real' | 'simulated' | ''>(''); // 帧来源
  const [isVideoFullscreen, setIsVideoFullscreen] = useState(false);
  
  // Tracking and Recognition state
  const [isTrackingEnabled, setIsTrackingEnabled] = useState(false);
  const [isRecognitionEnabled, setIsRecognitionEnabled] = useState(false);
  const [trackingStatus, setTrackingStatus] = useState<any>(null);
  const [recognitionStatus, setRecognitionStatus] = useState<any>(null);
  
  // 视觉控制标签页状态
  const [visionTab, setVisionTab] = useState<'camera' | 'ptz'>('camera');  // camera: 基础摄像头 | ptz: 云台控制
  
  const [isScanning, setIsScanning] = useState(false);

  // Lifecycle
  useEffect(() => {
    fetchDevices();
    fetchJepaStatus();
    checkMasterStatus();
    checkCameraStatus(); // 初始化时检查摄像头状态
  }, []);

  // 检查并同步摄像头、跟踪和识别状态
  const checkCameraStatus = async () => {
    try {
      // 初始化时主动关闭后端摄像头并重置前端状态为 false。
      // 原因：后端 camera_state 是内存变量，页面刷新后若直接同步 is_open=true，
      // 前端 isCameraOpen 初始值已经是 false，useEffect 不会再触发，WebSocket 不会建立。
      // 统一从关闭状态出发，用户点开关按钮时 false→true 才能正确建立 WebSocket。
      await apiClient.closeCamera();
      setIsCameraOpen(false);
      setCameraFrame('');

      // 跟踪和识别状态仍然同步（后端重置后这两个也会是 false，但读一次无害）
      const trackRes = await apiClient.get<{ tracking_enabled: boolean, tracker_type?: string }>('/api/camera/tracking/status');
      if (trackRes.success && trackRes.data) {
        setIsTrackingEnabled(trackRes.data.tracking_enabled);
        setTrackingStatus(trackRes.data);
      }
      
      const recogRes = await apiClient.get<{ recognizing_enabled: boolean, recognized_objects_count?: number }>('/api/camera/recognition/status');
      if (recogRes.success && recogRes.data) {
        setIsRecognitionEnabled(recogRes.data.recognizing_enabled);
        setRecognitionStatus(recogRes.data);
      }
    } catch (error) {
      console.error('检查摄像头状态失败:', error);
    }
  };

  const checkMasterStatus = async () => {
     try {
       const res = await apiClient.get<{ master_control_active: boolean }>('/api/ai-control/master-control/status');
       setIsMasterActive(res.data?.master_control_active || false);
     } catch (e) {}
  };

  const fetchDevices = async () => {
    const res = await apiClient.getDevices();
    if (res.success && res.data) setDevices(res.data);
  };

  const fetchJepaStatus = async () => {
    const res = await apiClient.getJepaDtmpcStatus();
    if (res.success && res.data) {
      setIsJepaActive(res.data.is_active);
      setJepaModelStatus(res.data.model_status);
    }
  };

  const scanDevices = async () => {
    setIsScanning(true);
    const res = await apiClient.scanDevices();
    if (res.success && res.data) setDevices(res.data);
    setIsScanning(false);
  };

  // Actions
  const handleMasterToggle = async () => {
    const newStatus = !isMasterActive;
    const res = await apiClient.activateMasterControl(newStatus);
    if (res.success) setIsMasterActive(newStatus);
  };

  const toggleJepa = async () => {
    const newStatus = !isJepaActive;
    try {
      const res = await apiClient.activateJepaDtmpc({
        controller_params: { control_switch: newStatus, startup_mode: 'cold' },
        mv_params: { 
          operation_range: [-100, 100],
          rate_limits: [-10, 10],
          action_cycle: 1.0
        },
        cv_params: { 
          setpoint: 50,
          safety_range: [-200, 200],
          weights: 1.0
        },
        model_params: { 
          prediction_horizon: 10, 
          control_horizon: 5,
          system_gain: 1.0,
          time_delay: 1,
          time_constant: 5
        },
        jepa_params: { 
          enabled: newStatus, 
          embedding_dim: 10, 
          prediction_horizon: 20,
          input_dim: 3,
          output_dim: 1,
          training_steps: 100
        }
      } as any);
      if (res.success) setIsJepaActive(newStatus);
    } catch (error) {
      console.error('激活JEPA-DT-MPC失败:', error);
      // 可以添加用户友好的错误提示
    }
  };

  const toggleCamera = async () => {
    try {
      if (isCameraOpen) {
        // 关闭摄像头前先停止跟踪和识别
        if (isTrackingEnabled) {
          await apiClient.stopTracking();
          setIsTrackingEnabled(false);
          setTrackingStatus(null);
        }
        if (isRecognitionEnabled) {
          await apiClient.stopRecognition();
          setIsRecognitionEnabled(false);
          setRecognitionStatus(null);
        }
        
        // 关闭摄像头
        const res = await apiClient.closeCamera();
        if (res.success) {
          setIsCameraOpen(false);
          setCameraFrame('');
          console.log('摄像头已关闭');
        } else {
          console.error('关闭摄像头失败:', res);
        }
      } else {
        // 打开摄像头
        const res = await apiClient.openCamera();
        if (res.success) {
          setIsCameraOpen(true);
          console.log('摄像头已打开');
        } else {
          setCameraError("打开摄像头失败");
          console.error('打开摄像头失败:', res);
        }
      }
    } catch (error) {
      console.error('摄像头操作失败:', error);
      setCameraError('摄像头操作失败');
    }
  };

  // 切换跟踪功能
  const toggleTracking = async () => {
    // 检查摄像头是否开启
    if (!isCameraOpen) {
      console.warn('请先打开摄像头');
      setCameraError('请先打开摄像头');
      return;
    }
    
    try {
      if (isTrackingEnabled) {
        const res = await apiClient.stopTracking();
        if (res.success) {
          setIsTrackingEnabled(false);
          setTrackingStatus(null);
          console.log('跟踪已停止');
        }
      } else {
        const res = await apiClient.startTracking('CSRT');
        if (res.success) {
          setIsTrackingEnabled(true);
          // 获取跟踪状态
          const status = await apiClient.get<{ tracking_enabled: boolean, tracker_type?: string }>('/api/camera/tracking/status');
          if (status.data) setTrackingStatus(status.data);
          console.log('跟踪已启动');
        }
      }
    } catch (error) {
      console.error('跟踪切换失败:', error);
    }
  };

  // 切换识别功能
  const toggleRecognition = async () => {
    // 检查摄像头是否开启
    if (!isCameraOpen) {
      console.warn('请先打开摄像头');
      setCameraError('请先打开摄像头');
      return;
    }
    
    try {
      if (isRecognitionEnabled) {
        const res = await apiClient.stopRecognition();
        if (res.success) {
          setIsRecognitionEnabled(false);
          setRecognitionStatus(null);
          console.log('识别已停止');
        }
      } else {
        const res = await apiClient.startRecognition('haar');
        if (res.success) {
          setIsRecognitionEnabled(true);
          // 获取识别状态
          const status = await apiClient.get<{ recognizing_enabled: boolean, recognized_objects_count?: number }>('/api/camera/recognition/status');
          if (status.data) setRecognitionStatus(status.data);
          console.log('识别已启动');
        }
      }
    } catch (error) {
      console.error('识别切换失败:', error);
    }
  };

  // 处理设备连接切换
  const handleToggleConnection = async (deviceId: number) => {
    const device = devices.find(d => d.id === deviceId);
    if (!device) return;

    try {
      const newConnectionState = !device.connected;
      const res = await apiClient.toggleDeviceConnection(deviceId, newConnectionState);
      
      if (res.success) {
        // 更新设备列表
        setDevices(prev => prev.map(d => 
          d.id === deviceId 
            ? { ...d, connected: newConnectionState, status: newConnectionState ? 'online' : 'offline' }
            : d
        ));
      }
    } catch (error) {
      console.error('切换设备连接失败:', error);
    }
  };

  // 处理设备控制
  const handleDeviceControl = async (deviceId: number) => {
    const device = devices.find(d => d.id === deviceId);
    if (!device || !device.connected) return;

    try {
      // 这里可以打开设备控制对话框或执行特定控制操作
      console.log('控制设备:', device.name);
      // 示例：发送控制命令
      const res = await apiClient.controlDevice(deviceId, { action: 'status_check' });
      if (res.success) {
        console.log('设备控制成功:', res.data);
      }
    } catch (error) {
      console.error('设备控制失败:', error);
    }
  };

  // Camera Frame Loop - 使用 WebSocket 替代高频轮询（解决429限流问题）
  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const connect = () => {
      if (stopped || !isCameraOpen) return;

      // ⚠️ 必须连到 Vite 开发服务器自身（window.location.host = localhost:3000）
      // 让 Vite proxy 中转到后端 8001，否则浏览器直连 8001 会跨域失败
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/camera/ws/frame`;

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('摄像头 WebSocket 连接成功:', wsUrl);
        setCameraError('');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.success && data.frame_base64) {
            // 根据后端返回的 format 字段选择正确的 MIME 类型
            // 真实摄像头返回 jpeg，模拟帧返回 png
            const mime = data.format === 'jpeg' ? 'image/jpeg' : 'image/png';
            setCameraFrame(`data:${mime};base64,${data.frame_base64}`);
            setCameraSource(data.source === 'real' ? 'real' : 'simulated');
          } else if (!data.success) {
            console.warn('摄像头帧获取失败:', data.message);
          }
        } catch (e) {
          console.error('WebSocket 消息解析错误:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('摄像头 WebSocket 错误:', error);
        setCameraError('摄像头链路连接失败，请确认后端服务已启动');
      };

      ws.onclose = () => {
        console.log('摄像头 WebSocket 连接关闭');
        // 3 秒后自动重连（摄像头仍处于开启状态时）
        if (!stopped && isCameraOpen) {
          retryTimer = setTimeout(connect, 3000);
        }
      };
    };

    if (isCameraOpen) {
      connect();
    } else {
      // 摄像头关闭时清除画面
      setCameraFrame('');
      setCameraError('');
      setCameraSource('');
    }

    // 清理函数：组件卸载或摄像头关闭时断开 WebSocket
    return () => {
      stopped = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (ws) {
        ws.close();
        ws = null;
      }
    };
  }, [isCameraOpen]);

  // Voice Control logic (simplified for brevity but functional)
  const toggleVoice = () => {
    if (isVoiceActive) {
      voiceRecognitionRef.current?.stop();
      setIsVoiceActive(false);
    } else {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = true;
        recognition.onresult = (event: any) => {
          const cmd = event.results[event.results.length - 1][0].transcript;
          setLastCommand(cmd);
          if (cmd.includes('开启主控')) handleMasterToggle();
        };
        recognition.start();
        voiceRecognitionRef.current = recognition;
        setIsVoiceActive(true);
      }
    }
  };

  return (
    <div className="space-y-8 pb-20">
      {/* 全屏视频模态框 */}
      <AnimatePresence>
        {isVideoFullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[9999] bg-black flex flex-col"
            onClick={() => setIsVideoFullscreen(false)}
          >
            {/* 顶部工具栏 */}
            <div
              className="flex items-center justify-between px-4 py-2 bg-black/80 backdrop-blur-sm border-b border-white/10"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center space-x-2">
                {isCameraOpen && (
                  <>
                    <div className="w-2 h-2 rounded-full bg-cyber-emerald animate-pulse" />
                    <span className="text-xs font-bold text-cyber-emerald uppercase tracking-widest">实时神经馈送</span>
                  </>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleCamera}
                  className={cn(
                    "flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all border",
                    isCameraOpen
                      ? "bg-red-500/20 text-red-400 border-red-500/30 hover:bg-red-500/30"
                      : "bg-cyber-cyan/20 text-cyber-cyan border-cyber-cyan/30 hover:bg-cyber-cyan/30"
                  )}
                >
                  <Power size={12} />
                  <span>{isCameraOpen ? '关闭' : '开启摄像头'}</span>
                </button>
                <button
                  onClick={() => setIsVideoFullscreen(false)}
                  className="p-1.5 rounded-lg bg-white/10 border border-white/20 text-gray-300 hover:text-white hover:bg-white/20 transition-all"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* 视频内容区 */}
            <div className="flex-1 flex items-center justify-center overflow-hidden">
              {isCameraOpen ? (
                cameraFrame ? (
                  <img
                    src={cameraFrame}
                    className="max-w-full max-h-full object-contain"
                    alt="Camera Feed"
                    onClick={e => e.stopPropagation()}
                  />
                ) : (
                  <div className="text-cyber-cyan text-sm animate-pulse font-mono">建立上行链路...</div>
                )
              ) : (
                <div className="flex flex-col items-center text-gray-600">
                  <Video size={64} className="mb-4 opacity-20" />
                  <span className="text-sm uppercase font-bold tracking-widest">馈送离线 — 点击开启摄像头</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-black tracking-tighter text-white mb-2 uppercase">
            控制 <span className="text-cyber-cyan">中心</span>
          </h1>
          <p className="text-gray-500 font-medium tracking-tight uppercase text-xs">AI设备编排与优化</p>
        </div>
        
        <div className="flex items-center space-x-3 bg-white/5 p-2 rounded-2xl border border-white/5 backdrop-blur-md">
           <button 
             onClick={toggleVoice}
             className={cn(
               "p-3 rounded-xl transition-all flex items-center space-x-2",
               isVoiceActive ? "bg-cyber-rose/20 text-cyber-rose neon-glow-purple" : "text-gray-400 hover:text-white"
             )}
           >
             {isVoiceActive ? <Mic size={20} /> : <MicOff size={20} />}
             <span className="text-xs font-bold uppercase">{isVoiceActive ? "监听中" : "语音控制"}</span>
           </button>
           
           <div className="w-[1px] h-6 bg-white/10" />

           <button 
             onClick={handleMasterToggle}
             className={cn(
               "px-6 py-3 rounded-xl font-bold flex items-center space-x-2 transition-all",
               isMasterActive 
                ? "bg-cyber-rose text-white shadow-lg shadow-cyber-rose/40" 
                : "bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/20 neon-glow-cyan"
             )}
           >
             <Power size={18} />
             <span>{isMasterActive ? "关闭主控" : "激活主控"}</span>
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Device Matrix & Presets */}
        <div className="lg:col-span-8 space-y-6">
          {/* Presets Bento */}
          <BentoCard title="AI运行模式" description="预定义神经配置文件" icon={Settings}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
              {mockPresets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => {
                    setSelectedPreset(preset);
                    setSelectedDevices(preset.devices);
                  }}
                  className={cn(
                    "p-5 rounded-2xl border text-left transition-all relative overflow-hidden group",
                    selectedPreset.id === preset.id 
                      ? "bg-cyber-cyan/10 border-cyber-cyan/40" 
                      : "bg-white/5 border-white/5 hover:border-white/10"
                  )}
                >
                  <div className={cn(
                    "mb-4 w-10 h-10 rounded-lg flex items-center justify-center transition-all",
                    selectedPreset.id === preset.id ? "bg-cyber-cyan text-black" : "bg-white/5 text-gray-500"
                  )}>
                    <Zap size={20} />
                  </div>
                  <h4 className="font-bold text-white mb-1">{preset.name}</h4>
                  <p className="text-[10px] text-gray-500 uppercase leading-relaxed tracking-wider">{preset.description}</p>
                  
                  {selectedPreset.id === preset.id && (
                    <motion.div layoutId="active-preset" className="absolute top-2 right-2">
                      <CheckCircle size={16} className="text-cyber-cyan" />
                    </motion.div>
                  )}
                </button>
              ))}
            </div>
          </BentoCard>

          {/* Device Matrix */}
          <div className="flex items-center justify-between mb-2">
             <h3 className="text-lg font-bold text-white uppercase tracking-tighter flex items-center space-x-2">
                <Wifi size={18} className="text-cyber-cyan" />
                <span>设备矩阵</span>
             </h3>
             <button 
               onClick={scanDevices}
               disabled={isScanning}
               className="text-[10px] font-bold text-cyber-cyan uppercase tracking-widest flex items-center space-x-2 hover:opacity-80 disabled:opacity-50"
             >
                <RefreshCw size={12} className={isScanning ? "animate-spin" : ""} />
                <span>{isScanning ? "扫描中..." : "重新扫描环境"}</span>
             </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             {devices.map((device) => (
               <DeviceCard 
                 key={device.id}
                 device={device}
                 isSelected={selectedDevices.includes(device.id)}
                 onSelect={(id) => setSelectedDevices(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])}
                 onToggleConnection={handleToggleConnection}
                 onControl={handleDeviceControl}
               />
             ))}
             {devices.length === 0 && [1,2,3,4].map(i => (
               <div key={i} className="h-48 glass-card rounded-2xl animate-pulse" />
             ))}
          </div>
        </div>

        {/* Right Column: Intelligence & Vision */}
        <div className="lg:col-span-4 space-y-6">
           {/* Visual Feed */}
           <BentoCard title="视觉智能" description="神经流馈送" icon={Video}>
              {/* 标签页切换 */}
              <div className="flex items-center space-x-2 mb-4">
                <button
                  onClick={() => setVisionTab('camera')}
                  className={cn(
                    "flex-1 px-3 py-2 rounded-lg text-xs font-bold transition-all",
                    visionTab === 'camera'
                      ? "bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30"
                      : "bg-gray-700/50 text-gray-400 border border-gray-600/30 hover:bg-gray-700"
                  )}
                >
                  📹 基础监控
                </button>
                <button
                  onClick={() => setVisionTab('ptz')}
                  className={cn(
                    "flex-1 px-3 py-2 rounded-lg text-xs font-bold transition-all",
                    visionTab === 'ptz'
                      ? "bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30"
                      : "bg-gray-700/50 text-gray-400 border border-gray-600/30 hover:bg-gray-700"
                  )}
                >
                  🎯 PTZ云台
                </button>
              </div>
              
              {/* 基础摄像头监控 */}
              {visionTab === 'camera' && (
                <>
                  <div className="mt-4 relative rounded-xl overflow-hidden aspect-video bg-black border border-white/5">
                    {isCameraOpen ? (
                      cameraFrame ? (
                        <img src={cameraFrame} className="w-full h-full object-cover" alt="Feed" />
                      ) : (
                        <div className="absolute inset-0 flex items-center justify-center text-xs text-cyber-cyan animate-pulse font-mono">建立上行链路...</div>
                      )
                    ) : (
                      <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-600">
                        <Video size={40} className="mb-2 opacity-20" />
                        <span className="text-[10px] uppercase font-bold tracking-widest">馈送离线</span>
                      </div>
                    )}

                    {isCameraOpen && (
                      <div className="absolute top-4 left-4 flex items-center space-x-2 px-2 py-1 rounded bg-black/60 backdrop-blur-sm border border-cyber-emerald/30">
                        <div className="w-1.5 h-1.5 rounded-full bg-cyber-emerald animate-pulse" />
                        <span className="text-[8px] font-bold text-cyber-emerald uppercase tracking-tighter">实时神经馈送</span>
                        {cameraSource === 'real' && (
                          <span className="text-[8px] px-1 rounded bg-cyber-emerald/20 text-cyber-emerald border border-cyber-emerald/40">真实</span>
                        )}
                        {cameraSource === 'simulated' && (
                          <span className="text-[8px] px-1 rounded bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">模拟</span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* 摄像头控制栏（始终可见） */}
                  <div className="mt-2 flex items-center justify-between px-1">
                    <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">
                      {isCameraOpen ? '摄像头运行中' : '摄像头已关闭'}
                    </span>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={toggleCamera}
                        className={cn(
                          "flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all border",
                          isCameraOpen
                            ? "bg-red-500/20 text-red-400 border-red-500/30 hover:bg-red-500/30"
                            : "bg-cyber-cyan/20 text-cyber-cyan border-cyber-cyan/30 hover:bg-cyber-cyan/30"
                        )}
                      >
                        <Power size={12} />
                        <span>{isCameraOpen ? '关闭' : '开启摄像头'}</span>
                      </button>
                      <button className="p-1.5 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white transition-all" onClick={() => setIsVideoFullscreen(true)}>
                        <Maximize2 size={12} />
                      </button>
                    </div>
                  </div>
                  <div className="mt-4 space-y-2">
                    <p className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">AI视觉控制</p>
                    
                    {/* 跟踪控制 */}
                    <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-400">目标跟踪</span>
                        {isTrackingEnabled && (
                          <span className="text-[8px] px-2 py-0.5 rounded bg-green-500/20 text-green-400 border border-green-500/30">CSRT</span>
                        )}
                      </div>
                      <button
                        onClick={toggleTracking}
                        className={cn(
                          "px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all",
                          isTrackingEnabled
                            ? "bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30"
                            : "bg-gray-700/50 text-gray-400 border border-gray-600/30 hover:bg-cyber-cyan/20 hover:text-cyber-cyan hover:border-cyber-cyan/30",
                          !isCameraOpen && "opacity-70"
                        )}
                      >
                        {isTrackingEnabled ? '停止' : '启动'}
                      </button>
                    </div>
                    
                    {/* 识别控制 */}
                    <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-400">人脸识别</span>
                        {isRecognitionEnabled && (
                          <span className="text-[8px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">Haar</span>
                        )}
                      </div>
                      <button
                        onClick={toggleRecognition}
                        className={cn(
                          "px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all",
                          isRecognitionEnabled
                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30"
                            : "bg-gray-700/50 text-gray-400 border border-gray-600/30 hover:bg-cyber-cyan/20 hover:text-cyber-cyan hover:border-cyber-cyan/30",
                          !isCameraOpen && "opacity-70"
                        )}
                      >
                        {isRecognitionEnabled ? '停止' : '启动'}
                      </button>
                    </div>
                    
                    {/* 状态提示 */}
                    {isTrackingEnabled && trackingStatus && (
                      <div className="p-2 rounded-lg bg-green-500/10 border border-green-500/20">
                        <p className="text-[10px] text-green-400">
                          🎯 正在跟踪目标 | 算法: {trackingStatus.tracker_type}
                        </p>
                        <p className="text-[8px] text-green-300/70 mt-1">
                          ℹ️ 画面中的绿色框会跟随目标移动（模拟摄像头转动）
                        </p>
                      </div>
                    )}
                    
                    {isRecognitionEnabled && recognitionStatus && (
                      <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
                        <p className="text-[10px] text-blue-400">
                          👤 正在识别人脸 | 检测到: {recognitionStatus.recognized_objects_count || 0} 个
                        </p>
                        <p className="text-[8px] text-blue-300/70 mt-1">
                          ℹ️ 画面中的蓝色框显示识别到的人脸位置
                        </p>
                      </div>
                    )}
                    
                    {!isCameraOpen && (
                      <div className="p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                        <p className="text-[10px] text-yellow-400">
                          ⚠️ 请先点击画面上的电源按钮打开摄像头
                        </p>
                      </div>
                    )}
                  </div>
                </>
              )}
              
              {/* PTZ云台控制 */}
              {visionTab === 'ptz' && (
                <PTZControl apiClient={apiClient} />
              )}
           </BentoCard>

           {/* JEPA-DT-MPC Control */}
           <BentoCard title="JEPA预测" description="自主MPC集成" icon={Activity}>
              <div className="flex items-center justify-between mb-4">
                 <div className="flex items-center space-x-2">
                    <div className={cn("w-2 h-2 rounded-full", isJepaActive ? "bg-cyber-emerald animate-pulse" : "bg-gray-700")} />
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">引擎 {isJepaActive ? "运行中" : "待机"}</span>
                 </div>
                 <button 
                   onClick={toggleJepa}
                   className={cn(
                     "text-[10px] font-bold px-3 py-1 rounded-full transition-all border",
                     isJepaActive 
                       ? "bg-cyber-rose/10 text-cyber-rose border-cyber-rose/20" 
                       : "bg-cyber-cyan/10 text-cyber-cyan border-cyber-cyan/20"
                   )}
                 >
                   {isJepaActive ? "断开" : "启动"}
                 </button>
              </div>

              <div className="h-40 w-full bg-white/5 rounded-xl border border-white/5 p-4 relative overflow-hidden">
                 <div className="absolute inset-0 flex items-center justify-center opacity-10">
                    <Activity size={80} className="text-cyber-cyan" />
                 </div>
                 <div className="relative z-10 flex flex-col h-full justify-between">
                    <div className="flex justify-between items-end">
                       <div>
                          <p className="text-[8px] text-gray-500 uppercase font-bold mb-1">预测权重</p>
                          <h4 className="text-2xl font-black text-white">0.842</h4>
                       </div>
                       <ArrowRight size={20} className="text-cyber-cyan mb-1" />
                    </div>
                    
                    <div className="space-y-2">
                       <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest">
                          <span className="text-gray-500">稳定性</span>
                          <span className="text-cyber-emerald">98.4%</span>
                       </div>
                       <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: "98%" }}
                            className="h-full bg-cyber-emerald"
                          />
                       </div>
                    </div>
                 </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3">
                 <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                    <p className="text-[8px] text-gray-500 uppercase font-bold mb-1">模型状态</p>
                    <p className="text-xs font-bold text-cyber-cyan uppercase">{jepaModelStatus}</p>
                 </div>
                 <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                    <p className="text-[8px] text-gray-500 uppercase font-bold mb-1">能源指数</p>
                    <p className="text-xs font-bold text-cyber-purple">0.024</p>
                 </div>
              </div>
           </BentoCard>

           {/* Voice Logs */}
           <AnimatePresence>
             {lastCommand && (
               <motion.div
                 initial={{ opacity: 0, y: 10 }}
                 animate={{ opacity: 1, y: 0 }}
                 exit={{ opacity: 0, scale: 0.95 }}
                 className="p-4 rounded-xl glass-morphism border border-cyber-cyan/20 bg-cyber-cyan/5"
               >
                 <div className="flex items-center space-x-2 mb-2">
                    <Mic size={14} className="text-cyber-cyan" />
                    <span className="text-[10px] font-bold text-cyber-cyan uppercase tracking-widest">最后接收的命令</span>
                 </div>
                 <p className="text-sm font-mono text-white/90">"{lastCommand}"</p>
               </motion.div>
             )}
           </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
