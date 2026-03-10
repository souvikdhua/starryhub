import React from 'react';
import { cn } from '../../lib/utils';

interface GaugeChartProps {
    value: number;
    max: number;
    threshold: number;
    title: string;
    subTitle: string;
    unit?: string;
}

export const GaugeChart: React.FC<GaugeChartProps> = ({
    value,
    max,
    threshold,
    title,
    subTitle,
    unit = "₹"
}) => {
    // Normalize value for percentage
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));
    const isDanger = value < threshold;

    // Angle calculations for semi-circle
    // Start 180 (left), End 0 (right).

    return (
        <div className="relative flex flex-col items-center justify-center p-6 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800">
            <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200 mb-1">{title}</h3>
            <p className="text-xs text-muted-foreground mb-6 uppercase tracking-wider">{subTitle}</p>

            <div className="relative w-full aspect-[2/1] max-w-[300px]">
                <svg viewBox="0 0 200 110" className="w-full h-full overflow-visible">
                    {/* Defs for gradients */}
                    <defs>
                        <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="var(--color-danger)" />
                            <stop offset={`${(threshold / max) * 100}% `} stopColor="var(--color-danger)" />
                            <stop offset={`${(threshold / max) * 100}% `} stopColor="var(--color-success)" />
                            <stop offset="100%" stopColor="var(--color-success)" />
                        </linearGradient>
                        <marker id="arrow" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto">
                            <path d="M0,0 L10,5 L0,10" fill="currentColor" />
                        </marker>
                    </defs>

                    {/* Background Arc (Gray) */}
                    <path
                        d="M 20 100 A 80 80 0 0 1 180 100"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="12"
                        strokeLinecap="round"
                        className="text-slate-100 dark:text-slate-800"
                    />

                    {/* Active Arc (Colored) */}
                    <path
                        d="M 20 100 A 80 80 0 0 1 180 100"
                        fill="none"
                        stroke={isDanger ? "#ef4444" : "#10b981"} // color-danger or color-success
                        strokeWidth="12"
                        strokeLinecap="round"
                        strokeDasharray="251.2"
                        strokeDashoffset={251.2 - (251.2 * percentage / 100)}
                        className="transition-all duration-1000 ease-out drop-shadow-sm"
                    />

                    {/* Threshold Marker (The "Red Line" requirement) */}
                    {/* 5L threshold on 12L max. Angle = 180 * (1 - 5/12) because 0 is right, 180 is left? 
              Actually standard gauge: Left (180 deg) to Right (0 deg).
              Let's convert value to angle (deg).
              0 value = 180 deg.
              Max value = 0 deg.
              Angle = 180 - (value/max)*180.
          */}
                    {(() => {
                        const thresholdAngle = 180 - (threshold / max) * 180;
                        const r = 80;
                        // Convert degrees to radians for JS Math (which expects radians) 
                        // but SVG rotate transform uses degrees.
                        // Position on the arc:
                        const rad = (thresholdAngle * Math.PI) / 180;
                        // Center 100,100. y is up in math, down in svg.
                        // x = 100 + r * cos(rad)  (Note: standard unit circle starts at 3 o'clock aka 0deg)
                        // In our gauge: 180deg is left, 0deg is right. Matches unit circle.
                        // But we want the arc to go from left (180) to right (0).
                        // cos(180) = -1 -> x=20. cos(0)=1 -> x=180. Correct.
                        // y = 100 - r * sin(rad). (Minus because SVG y is down).
                        const x = 100 + (r + 15) * Math.cos(rad); // Push it out a bit
                        const y = 100 - (r + 15) * Math.sin(rad);

                        return (
                            <g>
                                <line
                                    x1={100 + (r - 6) * Math.cos(rad)}
                                    y1={100 - (r - 6) * Math.sin(rad)}
                                    x2={100 + (r + 6) * Math.cos(rad)}
                                    y2={100 - (r + 6) * Math.sin(rad)}
                                    stroke="#ef4444"
                                    strokeWidth="3"
                                />
                                <text x={x} y={y} fontSize="10" textAnchor="middle" className="fill-red-500 font-bold">
                                    {(threshold / 100000).toFixed(1)}L
                                </text>
                            </g>
                        )
                    })()}

                    {/* Needle */}
                    {(() => {
                        const currentAngle = 180 - (percentage / 100) * 180;
                        return (
                            <g className="transition-all duration-1000 ease-out" style={{ transform: `rotate(${90 - currentAngle}deg)`, transformOrigin: '100px 100px' }}>
                                {/* We rotate the group. 0 rotation = pointing up (12 o clock)? 
                         Wait, let's just use rotation on the needle element directly based on the angle.
                         Standard 0 rotation for a vertical line is up.
                         Our angles: 180 (Left) -> 0 (Right).
                         If we draw needle pointing LEFT at rest, we rotate it?
                         Let's draw needle pointing RIGHT (0 deg).
                         Then rotate it -(180 - angle)?
                         Actually simple:
                         Draw needle from center to right.
                         Rotate it - (180 - angle).
                     */}
                                <line
                                    x1="100" y1="100"
                                    x2="170" y2="100"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                    className="text-slate-800 dark:text-slate-200"
                                    strokeLinecap="round"
                                    transform={`rotate(${- 1 * (180 - (percentage / 100) * 180)} 100 100)`}
                                />
                                <circle cx="100" cy="100" r="6" className="fill-slate-800 dark:fill-slate-200" />
                            </g>
                        )
                    })()}
                </svg>

                {/* Needle Value Text */}
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 flex flex-col items-center">
                    <span className={cn(
                        "text-3xl font-bold tracking-tight font-mono",
                        isDanger ? "text-red-600" : "text-emerald-600"
                    )}>
                        {unit}{(value / 100000).toFixed(2)}L
                    </span>
                    <span className="text-xs text-slate-400 font-medium">Current Balance</span>
                </div>
            </div>

            {/* Legend / Status */}
            <div className="mt-6 flex items-center gap-2 text-sm bg-slate-50 dark:bg-slate-800/50 px-3 py-1.5 rounded-full">
                <div className={cn("w-2 h-2 rounded-full animate-pulse", isDanger ? "bg-red-500" : "bg-emerald-500")}></div>
                <span className="text-muted-foreground font-medium">
                    {isDanger ? "Below Emergency Threshold!" : "Healthy Balance"}
                </span>
            </div>
        </div>
    );
};
