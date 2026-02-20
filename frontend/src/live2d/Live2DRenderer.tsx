/**
 * Live2D Renderer - Handles Live2D model rendering with PixiJS
 */

import { useEffect, useRef, useState } from 'react';
import { Application } from 'pixi.js';
import { Live2DModel } from 'pixi-live2d-display';
import type { Live2DModelConfig, Live2DParam, Emotion } from '../types';

interface Live2DRendererProps {
  config: Live2DModelConfig;
  className?: string;
  onModelLoaded?: () => void;
  onError?: (error: Error) => void;
}

// emotion to parameter mappings
const EMOTION_PARAMS: Record<Emotion, Live2DParam[]> = {
  neutral: [
    { name: 'ParamEyeLOpen', value: 1 },
    { name: 'ParamEyeROpen', value: 1 },
    { name: 'ParamBrowLY', value: 0 },
    { name: 'ParamBrowRY', value: 0 },
    { name: 'ParamBrowLX', value: 0 },
    { name: 'ParamBrowRX', value: 0 },
    { name: 'ParamBrowLAngle', value: 0 },
    { name: 'ParamBrowRAngle', value: 0 },
    { name: 'ParamMouthForm', value: 0 },
  ],
  happy: [
    { name: 'ParamEyeLOpen', value: 1 },
    { name: 'ParamEyeROpen', value: 1 },
    { name: 'ParamBrowLY', value: -0.3 },
    { name: 'ParamBrowRY', value: -0.3 },
    { name: 'ParamMouthForm', value: 0.5 },
  ],
  sad: [
    { name: 'ParamEyeLOpen', value: 0.7 },
    { name: 'ParamEyeROpen', value: 0.7 },
    { name: 'ParamBrowLY', value: 0.3 },
    { name: 'ParamBrowRY', value: 0.3 },
    { name: 'ParamBrowLAngle', value: 0.2 },
    { name: 'ParamBrowRAngle', value: -0.2 },
    { name: 'ParamMouthForm', value: -0.3 },
  ],
  angry: [
    { name: 'ParamEyeLOpen', value: 0.8 },
    { name: 'ParamEyeROpen', value: 0.8 },
    { name: 'ParamBrowLY', value: 0.4 },
    { name: 'ParamBrowRY', value: 0.4 },
    { name: 'ParamBrowLAngle', value: -0.3 },
    { name: 'ParamBrowRAngle', value: 0.3 },
    { name: 'ParamMouthForm', value: -0.2 },
  ],
  surprised: [
    { name: 'ParamEyeLOpen', value: 1.5 },
    { name: 'ParamEyeROpen', value: 1.5 },
    { name: 'ParamBrowLY', value: -0.5 },
    { name: 'ParamBrowRY', value: -0.5 },
    { name: 'ParamMouthForm', value: 0.3 },
  ],
};

export function Live2DRenderer({
  config,
  className = '',
  onModelLoaded,
  onError,
}: Live2DRendererProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null!);
  const appRef = useRef<Application | null>(null);
  const modelRef = useRef<Live2DModel | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Initialize PixiJS application and load Live2D model
  useEffect(() => {
    if (!canvasRef.current) return;

    let app: Application;
    let model: Live2DModel | null = null;

    const initPixi = async () => {
      try {
        // Create PixiJS application
        app = new Application({
          view: canvasRef.current,
          width: window.innerWidth,
          height: window.innerHeight,
          backgroundAlpha: 0,
          resolution: window.devicePixelRatio || 1,
          autoDensity: true,
        });
        appRef.current = app;

        // Load Live2D model
        model = await Live2DModel.from(config.modelUrl);
        modelRef.current = model;

        // Add model to stage
        app.stage.addChild(model);

        // Scale and center the model
        const scale = Math.min(
          (window.innerWidth * 0.8) / model.width,
          (window.innerHeight * 0.8) / model.height
        );
        model.scale.set(scale);
        model.x = window.innerWidth / 2;
        model.y = window.innerHeight / 2;

        // Enable auto-breathing
        // model.motion('idle', 0);

        setIsLoaded(true);
        onModelLoaded?.();
      } catch (error) {
        console.error('Failed to load Live2D model:', error);
        onError?.(error as Error);
      }
    };

    initPixi();

    // Handle window resize
    const handleResize = () => {
      if (!app || !model) return;

      app.renderer.resize(window.innerWidth, window.innerHeight);

      const scale = Math.min(
        (window.innerWidth * 0.8) / model.width,
        (window.innerHeight * 0.8) / model.height
      );
      model.scale.set(scale);
      model.x = window.innerWidth / 2;
      model.y = window.innerHeight / 2;
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (model) {
        app.stage.removeChild(model);
        model.destroy();
      }
      if (app) {
        app.destroy(true, true);
      }
    };
  }, [config, onModelLoaded, onError]);

  // Expose model control methods via ref
  useEffect(() => {
    if (!modelRef.current) return;

    // Make model methods available globally for debugging
    (window as any).live2dModel = modelRef.current;
  }, [isLoaded]);

  return (
    <canvas
      ref={canvasRef}
      className={`live2d-canvas ${className}`}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 1,
      }}
    />
  );
}

// Helper functions for model control
export function setModelParams(model: Live2DModel, params: Live2DParam[]): void {
  params.forEach(({ name, value }) => {
    // Access the model's parameters directly
    const id = (model as any).internalModel.settings.getMeshId(name);
    if (id !== undefined) {
      (model as any).internalModel.live2DModel.setParam(id, value);
    }
  });
}

export function setModelEmotion(model: Live2DModel, emotion: Emotion): void {
  const params = EMOTION_PARAMS[emotion] || EMOTION_PARAMS.neutral;
  setModelParams(model, params);
}

export function triggerMotion(
  model: Live2DModel,
  group: string,
  index: number,
  priority = 3
): void {
  model.motion(group, index, priority);
}
