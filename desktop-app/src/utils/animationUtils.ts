import { motion } from 'framer-motion';

// 优化的动画配置
export const optimizedAnimationConfig = {
  // 基础淡入动画
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: {
      duration: 0.3,
      ease: 'easeOut',
      // 使用GPU加速
      willChange: 'opacity'
    }
  },

  // 上移淡入动画
  fadeInUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: {
      duration: 0.4,
      ease: 'easeOut',
      // 使用GPU加速
      willChange: 'opacity, transform'
    }
  },

  // 缩放动画
  scaleIn: {
    initial: { scale: 0.95, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: {
      duration: 0.3,
      ease: 'easeOut',
      // 使用GPU加速
      willChange: 'transform, opacity'
    }
  },

  // 悬停效果
  hoverEffect: {
    whileHover: {
      y: -5,
      scale: 1.02,
      transition: {
        duration: 0.2,
        ease: 'easeOut',
        // 使用GPU加速
        willChange: 'transform'
      }
    }
  },

  // 卡片悬停效果
  cardHover: {
    whileHover: {
      y: -3,
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
      transition: {
        duration: 0.2,
        ease: 'easeOut',
        // 使用GPU加速
        willChange: 'transform, background-color'
      }
    }
  },

  // 容器动画 - 注意：此动画不直接应用于motion组件，需要特殊处理
  containerAnimation: {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  },

  // 子元素动画 - 注意：此动画不直接应用于motion组件，需要特殊处理
  itemAnimation: {
    initial: { opacity: 0, y: 20 },
    animate: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: 'easeOut'
      }
    }
  }
};

// 创建优化的动画组件
export const OptimizedMotion = motion;

// 动画性能监控
export const trackAnimationPerformance = (animationName: string) => {
  const startTime = performance.now();
  return () => {
    const endTime = performance.now();
    console.log(`${animationName} 动画执行时间: ${(endTime - startTime).toFixed(2)}ms`);
  };
};

// 检查设备性能并调整动画强度
export const getAnimationIntensity = () => {
  // 检查设备性能
  const isLowPerformance = 
    navigator.hardwareConcurrency < 4 ||
    (navigator as any).deviceMemory < 4 ||
    window.innerWidth < 768;

  return isLowPerformance ? 'low' : 'high';
};

// 根据设备性能获取优化的动画配置
export const getOptimizedAnimation = (animationType: string) => {
  const intensity = getAnimationIntensity();
  const baseConfig = optimizedAnimationConfig[animationType as keyof typeof optimizedAnimationConfig];

  if (!baseConfig) return baseConfig;

  if (intensity === 'low') {
    // 低性能设备使用更简单的动画
    const configWithTransition = baseConfig as any;
    return {
      ...baseConfig,
      transition: configWithTransition.transition ? {
        ...configWithTransition.transition,
        duration: (configWithTransition.transition?.duration || 0.3) * 0.7,
        // 禁用一些可能影响性能的效果
        ease: 'linear'
      } : undefined
    };
  }

  return baseConfig;
};

// 批量动画控制
export class AnimationManager {
  private activeAnimations: Set<string> = new Set();
  private performanceMode: 'high' | 'low' = 'high';

  constructor() {
    this.performanceMode = getAnimationIntensity() as 'high' | 'low';
  }

  startAnimation(id: string) {
    if (this.performanceMode === 'low' && this.activeAnimations.size > 3) {
      // 低性能模式下限制同时运行的动画数量
      return false;
    }

    this.activeAnimations.add(id);
    return true;
  }

  stopAnimation(id: string) {
    this.activeAnimations.delete(id);
  }

  clearAllAnimations() {
    this.activeAnimations.clear();
  }

  getActiveAnimationCount() {
    return this.activeAnimations.size;
  }
}

// 全局动画管理器实例
export const animationManager = new AnimationManager();
