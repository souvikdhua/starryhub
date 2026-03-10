
// Financial Constants based on User Prompt

export const FINANCIAL_DATA = {
    SAFE_CORPUS: {
        SCSS_PRINCIPAL: 3000000,
        SCSS_RATE: 0.082,
        FD_PRINCIPAL: 1000000,
        FD_RATE: 0.09,
        FD_PAYOUT_FREQ: 'monthly', // monthly
        SCSS_PAYOUT_FREQ: 'quarterly', // Apr, Jul, Oct, Jan
    },
    LIQUID_CORPUS: {
        INITIAL_BALANCE: 1200000,
        EMERGENCY_FUND: 500000,
        CONSTRUCTION_FUND: 700000,
        INTEREST_RATE: 0.07, // 7% p.a.
    },
    GROWTH_CORPUS: {
        INITIAL_LUMPSUM: 300000, // Year 1
        SIP_AMOUNT: 12000, // Starts Year 2
        GROWTH_RATE: 0.12, // 12% p.a.
    },
    EXPENSES: {
        LIVING_EXPENSES_MONTHLY: 30000,
        CONSTRUCTION_MONTHLY: 58333, // ~7L / 12
    },
    INCOME: {
        RENTAL_INCOME: 15000, // Starts Year 2
    },
    INFLATION_RATE: 0.06,
};
