import React from 'react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

// 基础骨架
export const Skeleton: React.FC<SkeletonProps> = ({ className }) => (
  <div className={cn('animate-pulse rounded-lg bg-white/5', className)} />
);

// 统计卡片骨架
export const StatCardSkeleton: React.FC = () => (
  <div className="p-6 rounded-2xl bg-white/3 border border-white/5">
    <div className="flex items-center justify-between">
      <div className="space-y-2">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-8 w-16" />
      </div>
      <Skeleton className="w-12 h-12 rounded-xl" />
    </div>
  </div>
);

// 列表条目骨架
export const ListItemSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-white/3 border border-white/5">
        <Skeleton className="w-8 h-8 rounded-lg shrink-0" />
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-3.5 w-3/4" />
          <Skeleton className="h-2.5 w-1/2" />
        </div>
        <Skeleton className="h-5 w-12 rounded-full" />
      </div>
    ))}
  </div>
);

// 图表骨架
export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 200 }) => (
  <div className="relative w-full rounded-xl overflow-hidden bg-white/3 border border-white/5" style={{ height }}>
    <div className="absolute inset-0 flex items-end justify-between gap-2 p-4">
      {Array.from({ length: 7 }).map((_, i) => (
        <Skeleton
          key={i}
          className="flex-1 rounded-t-sm"
          style={{ height: `${30 + Math.random() * 60}%` }}
        />
      ))}
    </div>
  </div>
);

// 表格骨架
export const TableSkeleton: React.FC<{ rows?: number; cols?: number }> = ({ rows = 5, cols = 4 }) => (
  <div className="rounded-xl overflow-hidden border border-white/5">
    {/* 表头 */}
    <div className="flex gap-4 p-4 bg-white/5 border-b border-white/5">
      {Array.from({ length: cols }).map((_, i) => (
        <Skeleton key={i} className="h-3.5 flex-1" />
      ))}
    </div>
    {/* 行 */}
    {Array.from({ length: rows }).map((_, rowIdx) => (
      <div key={rowIdx} className="flex gap-4 p-4 border-b border-white/3 last:border-0">
        {Array.from({ length: cols }).map((_, colIdx) => (
          <Skeleton key={colIdx} className={cn('h-3.5 flex-1', colIdx === 0 && 'w-6 shrink-0 flex-none')} />
        ))}
      </div>
    ))}
  </div>
);

// 全页加载动画
export const PageLoader: React.FC<{ message?: string }> = ({ message = '页面加载中' }) => (
  <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
    <div className="relative w-12 h-12">
      <motion.div
        className="absolute inset-0 rounded-full border-2 border-cyber-cyan/30"
        animate={{ rotate: 360 }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        style={{ borderTopColor: 'rgba(0, 242, 255, 0.9)' }}
      />
      <motion.div
        className="absolute inset-2 rounded-full border-2 border-cyber-purple/30"
        animate={{ rotate: -360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        style={{ borderTopColor: 'rgba(188, 19, 254, 0.9)' }}
      />
    </div>
    <p className="text-sm text-gray-500 animate-pulse font-medium">{message}</p>
  </div>
);

// 空状态
export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
    {icon && (
      <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 text-gray-500">
        {icon}
      </div>
    )}
    <h3 className="text-base font-semibold text-gray-300 mb-2">{title}</h3>
    {description && <p className="text-sm text-gray-600 max-w-xs">{description}</p>}
    {action && <div className="mt-6">{action}</div>}
  </div>
);
