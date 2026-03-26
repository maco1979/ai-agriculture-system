import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, Sprout, Activity, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

const BOTTOM_NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: '首页' },
  { path: '/chat', icon: Bot, label: 'AI对话' },
  { path: '/agriculture', icon: Sprout, label: '农业' },
  { path: '/monitoring', icon: Activity, label: '监控' },
  { path: '/settings', icon: Settings, label: '设置' },
];

export const MobileBottomNav: React.FC = () => {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 safe-area-bottom">
      <div className="glass-morphism border-t border-white/8 px-2 pt-2 pb-safe">
        <div className="flex items-center justify-around">
          {BOTTOM_NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => cn(
                'flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl transition-all min-w-0',
                isActive ? 'text-cyber-cyan' : 'text-gray-500 hover:text-gray-300'
              )}
            >
              {({ isActive }) => (
                <>
                  <div className="relative">
                    {isActive && (
                      <motion.div
                        layoutId="bottom-nav-indicator"
                        className="absolute inset-0 bg-cyber-cyan/15 rounded-lg -m-1.5 border border-cyber-cyan/20"
                        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                      />
                    )}
                    <item.icon size={22} className="relative z-10" />
                  </div>
                  <span className={cn(
                    'text-[10px] font-medium transition-colors',
                    isActive ? 'text-cyber-cyan' : 'text-gray-600'
                  )}>
                    {item.label}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
};
