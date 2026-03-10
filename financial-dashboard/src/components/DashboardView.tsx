import React from 'react';
import { GaugeChart } from './charts/GaugeChart';
import { CashFlowChart } from './charts/CashFlowChart';
import { MetricCard } from './MetricCard';
import { calculateYear1CashFlow } from '../utils/calculations';
import { FINANCIAL_DATA } from '../constants';
import { Wallet, PiggyBank, Briefcase } from 'lucide-react';

export const DashboardView: React.FC = () => {
    const cashFlowData = calculateYear1CashFlow();

    // Current Status (Simulate we are at Month 0 or average? Prompt says "Dashboard" so let's show initial state or specific month)
    // Let's assume dashboard shows "Current Month" stats. Let's pick Month 0 (Apr) as "This Month" for now.
    const currentMonthData = cashFlowData[0];

    return (
        <div className="space-y-6">
            {/* Top Row: Gauge + Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Gauge Section */}
                <div className="lg:col-span-1">
                    <GaugeChart
                        value={FINANCIAL_DATA.LIQUID_CORPUS.INITIAL_BALANCE}
                        max={1500000} // A bit more than 12L for visual space
                        threshold={FINANCIAL_DATA.LIQUID_CORPUS.EMERGENCY_FUND}
                        title="Liquid Hub Account"
                        subTitle="Funds Available"
                    />
                </div>

                {/* Metrics Grid */}
                <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <MetricCard
                        title="Monthly Salary"
                        value={`₹${FINANCIAL_DATA.EXPENSES.LIVING_EXPENSES_MONTHLY.toLocaleString()}`}
                        subValue="Living Expenses"
                        icon={Briefcase}
                    />
                    <MetricCard
                        title="Passive Income"
                        value={`₹${Math.round(currentMonthData.passiveIncome).toLocaleString()}`}
                        subValue="This Month"
                        icon={Wallet}
                        className="lg:col-span-2 sm:col-span-2 lg:col-span-1"
                    />
                    <MetricCard
                        title="Construction Fund"
                        value={`₹${FINANCIAL_DATA.LIQUID_CORPUS.CONSTRUCTION_FUND.toLocaleString()}`}
                        subValue="Remaining"
                        icon={PiggyBank}
                    />
                    {/* Extra card for totals? Maybe Total Corpus? */}
                    <MetricCard
                        title="Safe Corpus"
                        value={`₹${((FINANCIAL_DATA.SAFE_CORPUS.SCSS_PRINCIPAL + FINANCIAL_DATA.SAFE_CORPUS.FD_PRINCIPAL) / 100000).toFixed(1)}L`}
                        subValue="Fixed Capital"
                        icon={Wallet} // or Shield
                        className="bg-slate-50 dark:bg-slate-800/50"
                    />
                    <MetricCard
                        title="Emergency Fund"
                        value={`₹${(FINANCIAL_DATA.LIQUID_CORPUS.EMERGENCY_FUND / 100000).toFixed(1)}L`}
                        subValue="Do Not Touch"
                        icon={Wallet} // or Shield
                        className="bg-red-50 dark:bg-slate-800/50"
                    />
                </div>
            </div>

            {/* Bottom Row: Cash Flow Chart */}
            <div className="h-[400px]">
                <CashFlowChart data={cashFlowData} />
            </div>
        </div>
    );
};
