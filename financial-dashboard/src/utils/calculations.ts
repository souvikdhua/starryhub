import { FINANCIAL_DATA } from '../constants';

// Types
export interface MonthlyFlow {
    month: string;
    monthIndex: number;
    income: number;
    outflow: number;
    liquidBalance: number;
    constructionFundBalance: number;
    passiveIncome: number;
}

export interface YearProjection {
    year: number;
    safeCapital: number;
    growthCapital: number;
    totalWealth: number;
}

export interface InflationData {
    year: number;
    nominalIncome: number;
    realPurchasingPower: number;
}

// Year 1 Calculations
export const calculateYear1CashFlow = (): MonthlyFlow[] => {
    const months = [
        'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'
    ];

    let liquidBalance = FINANCIAL_DATA.LIQUID_CORPUS.INITIAL_BALANCE;
    let constructionBalance = FINANCIAL_DATA.LIQUID_CORPUS.CONSTRUCTION_FUND;

    const data: MonthlyFlow[] = [];

    months.forEach((month, index) => {
        // 1. Income
        const fdInterest = (FINANCIAL_DATA.SAFE_CORPUS.FD_PRINCIPAL * FINANCIAL_DATA.SAFE_CORPUS.FD_RATE) / 12;

        // SCSS pays quarterly: Apr 1 (we assume received at start, but for cashflow usually end of month view or start? 
        // Prompt says "Pays 61500 every quarter: Apr 1, Jul 1, Oct 1, Jan 1".
        // Let's assume the flow happens in that month.
        // However, if we start in April, the first payment is Apr 1.
        // If we assume the dashboard starts Apr 1st.
        const isQuarterlyMonth = ['Apr', 'Jul', 'Oct', 'Jan'].includes(month);
        const scssInterest = isQuarterlyMonth
            ? (FINANCIAL_DATA.SAFE_CORPUS.SCSS_PRINCIPAL * FINANCIAL_DATA.SAFE_CORPUS.SCSS_RATE) / 4
            : 0;

        // Liquid Balance Interest (Monthly on balance)
        // Interest credited monthly on the balance.
        // We calculate interest based on start of month balance? Or end?
        // Let's take start of month for simplicity or average. Using start of month.
        const savingsInterest = (liquidBalance * FINANCIAL_DATA.LIQUID_CORPUS.INTEREST_RATE) / 12;

        const totalIncome = fdInterest + scssInterest + savingsInterest;

        // 2. Outflow
        const livingExpenses = FINANCIAL_DATA.EXPENSES.LIVING_EXPENSES_MONTHLY;

        // Construction: ~58333/month for Year 1.
        // We should cap it if fund is empty, but prompt assumes it runs out exactly or close.
        let constructionExpense = FINANCIAL_DATA.EXPENSES.CONSTRUCTION_MONTHLY;
        if (constructionBalance < constructionExpense) {
            constructionExpense = constructionBalance;
        }

        const totalOutflow = livingExpenses + constructionExpense;

        // 3. Update Balances
        liquidBalance = liquidBalance + totalIncome - totalOutflow;
        constructionBalance = Math.max(0, constructionBalance - constructionExpense);

        data.push({
            month,
            monthIndex: index,
            income: totalIncome,
            outflow: totalOutflow,
            liquidBalance,
            constructionFundBalance: constructionBalance,
            passiveIncome: totalIncome,
        });
    });

    return data;
};

// 5-Year Projections
export const calculateWealthProjection = (): YearProjection[] => {
    const data: YearProjection[] = [];
    const safeCapital = FINANCIAL_DATA.SAFE_CORPUS.SCSS_PRINCIPAL + FINANCIAL_DATA.SAFE_CORPUS.FD_PRINCIPAL; // 40L constant

    let currentGrowthCapital = FINANCIAL_DATA.GROWTH_CORPUS.INITIAL_LUMPSUM; // Start Year 1 with 3L?
    // "Initial Lumpsum: 3 Lakhs (Invested in Year 1)."
    // "SIP: 12,000/month (Starts in Year 2)."

    // We'll project end of each year.
    for (let year = 1; year <= 5; year++) {
        // Growth Capital Logic
        // Year 1: Just the 3L grows? Or 3L added?
        // Let's assume 3L added at start of Year 1.
        // Interest for full year.
        // Year 2: SIP starts.

        const yearlyRate = FINANCIAL_DATA.GROWTH_CORPUS.GROWTH_RATE;

        if (year === 1) {
            // End of Year 1
            currentGrowthCapital = currentGrowthCapital * (1 + yearlyRate);
        } else {
            // Add SIPs for the year (12 * 12000 = 1.44L)
            // Approximation: SIPs grow for average half year? Or using FV formula.
            // Better: Monthly compounding visualization isn't needed, just yearly.
            // Standard FV of SIP = P * ({[1+i]^n - 1} / i) * (1+i)
            const annualSIP = FINANCIAL_DATA.GROWTH_CORPUS.SIP_AMOUNT * 12;
            // Growth on SIP (approx .5 of rate or just add it)
            // Let's be generous/simple: Add SIPs, then grow? No, SIP spread out.
            // Let's use simple logic: (Opening + SIP/2) * rate + SIP?
            // Let's stick to simple: Opening * 1.12 + AnnualSIP. (Slightly conservative on SIP usage)
            // Re-reading: "Assumed Growth Rate: 12% p.a."
            currentGrowthCapital = (currentGrowthCapital * (1 + yearlyRate)) + annualSIP;
        }

        data.push({
            year,
            safeCapital, // 40L Flat
            growthCapital: Math.round(currentGrowthCapital),
            totalWealth: Math.round(safeCapital + currentGrowthCapital)
        });
    }
    return data;
};

export const calculateInflationImpact = (): InflationData[] => {
    const data: InflationData[] = [];

    // Nominal Income: "Flat constant at 28,000" (Prompt says 28k? "Line 1... Flat line at 28000")
    // Let's verify where 28k comes from.
    // SCSS (30L * 8.2% = 2.46L/yr = 20,500/mo)
    // FD (10L * 9% = 90,000/yr = 7,500/mo)
    // Total = 28,000/mo. Correct.

    const nominalIncome = 28000;
    const inflationRate = FINANCIAL_DATA.INFLATION_RATE;

    for (let year = 1; year <= 5; year++) {
        // Real Power = Nominal / (1 + r)^n
        // Year 0 = 28000. Year 1 = 28000 / 1.06
        // Usually "Over 5 years" starts at Year 0 (Now).
        // Let's do Year 1 to 5.
        // If Year 1 is "Now", it's 28000.
        // If Year 1 is "One year from now", it's 28000/1.06.
        // Let's assume Year 1 is the start, so it hasn't eroded yet?
        // Actually, "Declining value... over 5 years".
        // Let's show Year 1 as baseline (28k), Year 2 as 28k / 1.06 etc.
        // Or Year 0 to 5?
        // Let's just output Year 1 to 5, where Year 1 is 28k.

        // Better: Year 1 = 28000
        // Year 2 = 28000 / 1.06
        // ...
        const realPurchasingPower = nominalIncome / Math.pow(1 + inflationRate, year - 1);

        data.push({
            year,
            nominalIncome,
            realPurchasingPower: Math.round(realPurchasingPower)
        });
    }

    return data;
};
