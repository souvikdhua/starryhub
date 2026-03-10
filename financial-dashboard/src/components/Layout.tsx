import React from 'react';
import { cn } from '../lib/utils';
import { LayoutDashboard, TrendingUp } from 'lucide-react';

interface LayoutProps {
    children: React.ReactNode;
    activeTab: 'dashboard' | 'projections';
    onTabChange: (tab: 'dashboard' | 'projections') => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, activeTab, onTabChange }) => {
    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-50 selection:bg-primary/20">
            {/* Header / Navbar */}
            <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
                            <span className="font-bold text-primary-foreground text-lg">H</span>
                        </div>
                        <span className="font-bold text-xl tracking-tight">Hub Account</span>
                    </div>

                    <nav className="flex items-center gap-1 bg-secondary/50 p-1 rounded-full">
                        <button
                            onClick={() => onTabChange('dashboard')}
                            className={cn(
                                "flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200",
                                activeTab === 'dashboard'
                                    ? "bg-white dark:bg-slate-800 shadow-sm text-primary"
                                    : "text-muted-foreground hover:text-foreground hover:bg-white/50 dark:hover:bg-slate-800/50"
                            )}
                        >
                            <LayoutDashboard className="w-4 h-4" />
                            Year 1 Dashboard
                        </button>
                        <button
                            onClick={() => onTabChange('projections')}
                            className={cn(
                                "flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200",
                                activeTab === 'projections'
                                    ? "bg-white dark:bg-slate-800 shadow-sm text-primary"
                                    : "text-muted-foreground hover:text-foreground hover:bg-white/50 dark:hover:bg-slate-800/50"
                            )}
                        >
                            <TrendingUp className="w-4 h-4" />
                            5-Year Wealth
                        </button>
                    </nav>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-in fade-in-50 slide-in-from-bottom-4 duration-500">
                {children}
            </main>

            <footer className="border-t py-6 mt-12 bg-white/50 dark:bg-slate-900/50">
                <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
                    <p>© {new Date().getFullYear()} Financial Hub. All calculations are strictly client-side.</p>
                </div>
            </footer>
        </div>
    );
};
