import React from 'react';
import { WealthChart, InflationChart } from './charts/ProjectionCharts';
import { calculateWealthProjection, calculateInflationImpact } from '../utils/calculations';

export const ProjectionsView: React.FC = () => {
    const wealthData = calculateWealthProjection();
    const inflationData = calculateInflationImpact();

    return (
        <div className="space-y-6">
            <div className="p-6 bg-gradient-to-r from-slate-900 to-slate-800 rounded-2xl text-white shadow-lg">
                <h2 className="text-2xl font-bold mb-2">5-Year Strategy Projector</h2>
                <p className="text-slate-300">Visualizing long-term wealth accumulation and inflation defense.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <WealthChart data={wealthData} />
                <InflationChart data={inflationData} />
            </div>
        </div>
    );
};
