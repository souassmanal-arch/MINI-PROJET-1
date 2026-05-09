/**
 * ============================================================
 * Mexora Analytics — Dashboard BI JavaScript
 * ============================================================
 * Génère des données simulées réalistes et crée tous les
 * graphiques Chart.js pour les 6 pages du dashboard.
 * ============================================================
 */

// ===== COULEURS DU DESIGN SYSTEM =====
const COLORS = {
    primary: '#6366f1', secondary: '#818cf8', gold: '#f59e0b',
    green: '#10b981', red: '#ef4444', orange: '#f97316', cyan: '#06b6d4',
    purple: '#a855f7', pink: '#ec4899', teal: '#14b8a6',
    palette: ['#6366f1','#f59e0b','#10b981','#ef4444','#06b6d4','#a855f7','#ec4899','#f97316','#14b8a6','#3b82f6'],
    gridColor: 'rgba(255,255,255,0.05)',
    textColor: '#94a3b8',
};

const MONTHS = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'];
const REGIONS = ['Tanger-Tétouan-Al Hoceïma','Casablanca-Settat','Rabat-Salé-Kénitra','Marrakech-Safi','Fès-Meknès','Souss-Massa','Oriental','Béni Mellal-Khénifra','Drâa-Tafilalet','Laâyoune-Sakia El Hamra'];
const CATEGORIES = ['Electronique','Mode','Alimentation'];
const PRODUCTS_TANGER = [
    {name:'iPhone 16 Pro 256Go',ca:1842000},
    {name:'MacBook Air M3',ca:1521000},
    {name:'Samsung Galaxy S24',ca:1205000},
    {name:'AirPods Pro 2',ca:892000},
    {name:'Nike Air Max 90',ca:756000},
    {name:'iPad Air M2',ca:698000},
    {name:'Dell XPS 15',ca:654000},
    {name:'Huile Argan Bio',ca:521000},
    {name:'Polo Ralph Lauren',ca:489000},
    {name:'Sac Michael Kors',ca:412000},
];
const BRANDS = ['Apple','Samsung','Nike','Xiaomi','Adidas','Zara','Levi\'s','Logitech'];

// ===== GÉNÉRATEUR DE DONNÉES RÉALISTES =====
function genMonthlyCA(base, volatility, trend) {
    const d = [];
    for (let i = 0; i < 12; i++) {
        const seasonal = 1 + 0.15 * Math.sin((i - 2) * Math.PI / 6);
        const val = base * seasonal * (1 + trend * i / 12) * (1 + (Math.random() - 0.5) * volatility);
        d.push(Math.round(val));
    }
    return d;
}

const DATA = {
    ca2026: genMonthlyCA(8500000, 0.12, 0.08),
    ca2025: genMonthlyCA(7800000, 0.10, 0.05),
    regionCA: [28500000, 42100000, 22800000, 18600000, 15200000, 11400000, 8900000, 6200000, 4100000, 2800000],
    catCA: [52000000, 31000000, 18500000],
    segments: {
        Gold:   { clients: 420,  orders: 3200,  ca: 48200000, basket: 15062 },
        Silver: { clients: 1850, orders: 8900,  ca: 35600000, basket: 4000  },
        Bronze: { clients: 4200, orders: 11200, ca: 17700000, basket: 1580  },
    },
    returns: { Electronique: 4.2, Mode: 6.1, Alimentation: 1.8 },
    returnsTrend: genMonthlyCA(4, 0.3, -0.02).map(v => Math.max(1, Math.min(8, v))),
    ramadan: { ca: 4200000, caHors: 2800000 },
};
DATA.totalCA = DATA.ca2026.reduce((a, b) => a + b, 0);
DATA.totalOrders = 23300;
DATA.totalClients = 6470;
DATA.basket = Math.round(DATA.totalCA / DATA.totalOrders);

// ===== CHART.JS DEFAULT CONFIG =====
Chart.defaults.color = COLORS.textColor;
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
Chart.defaults.plugins.legend.labels.padding = 20;

const defaultScaleOpts = {
    grid: { color: COLORS.gridColor, drawBorder: false },
    ticks: { padding: 8 },
};

function fmt(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + ' M';
    if (n >= 1e3) return (n / 1e3).toFixed(0) + ' K';
    return n.toLocaleString('fr-MA');
}
function fmtMAD(n) { return fmt(n) + ' MAD'; }

// ===== NAVIGATION =====
const navBtns = document.querySelectorAll('.nav-btn');
const pages = document.querySelectorAll('.page');
const pageTitle = document.getElementById('page-title');
const titles = {
    overview:'Vue d\'ensemble', revenue:'Évolution du CA',
    products:'Top Produits', segments:'Segments Clients',
    returns:'Taux de Retour', ramadan:'Effet Ramadan',
};

navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const target = btn.dataset.page;
        navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        pages.forEach(p => { p.classList.toggle('active', p.id === 'page-' + target); });
        pageTitle.textContent = titles[target] || target;
        document.getElementById('sidebar').classList.remove('open');
    });
});

document.getElementById('menu-toggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
});

// ===== KPI UPDATES =====
function updateKPIs() {
    document.getElementById('kpi-ca-value').textContent = fmtMAD(DATA.totalCA);
    document.getElementById('kpi-ca-change').textContent = '▲ +8.2% vs N-1';
    document.getElementById('kpi-orders-value').textContent = fmt(DATA.totalOrders);
    document.getElementById('kpi-orders-change').textContent = '▲ +12.4%';
    document.getElementById('kpi-basket-value').textContent = fmtMAD(DATA.basket);
    document.getElementById('kpi-basket-change').textContent = '▼ -2.1%';
    document.getElementById('kpi-basket-change').classList.add('negative');
    document.getElementById('kpi-clients-value').textContent = fmt(DATA.totalClients);
    document.getElementById('kpi-clients-change').textContent = '▲ +18.7%';
    document.getElementById('last-update-time').textContent = new Date().toLocaleString('fr-MA');

    // Revenue page KPIs
    document.getElementById('rev-current').textContent = fmtMAD(DATA.ca2026[11]);
    document.getElementById('rev-previous').textContent = fmtMAD(DATA.ca2026[10]);
    const evol = ((DATA.ca2026[11] - DATA.ca2026[10]) / DATA.ca2026[10] * 100).toFixed(1);
    document.getElementById('rev-evolution').textContent = (evol > 0 ? '+' : '') + evol + '%';
    document.getElementById('rev-top-region').textContent = 'Casablanca-Settat';

    // Segment KPIs
    document.getElementById('seg-gold').textContent = fmtMAD(DATA.segments.Gold.basket);
    document.getElementById('seg-silver').textContent = fmtMAD(DATA.segments.Silver.basket);
    document.getElementById('seg-bronze').textContent = fmtMAD(DATA.segments.Bronze.basket);

    // Ramadan KPIs
    document.getElementById('ram-ca').textContent = fmtMAD(DATA.ramadan.ca);
    document.getElementById('ram-ca-hors').textContent = fmtMAD(DATA.ramadan.caHors);
    const idx = (DATA.ramadan.ca / DATA.ramadan.caHors * 100).toFixed(0);
    document.getElementById('ram-index').textContent = idx + '% (+' + (idx - 100) + '%)';

    // Segments table
    const tbody = document.getElementById('table-segments-body');
    const totalSegCA = Object.values(DATA.segments).reduce((a, s) => a + s.ca, 0);
    tbody.innerHTML = '';
    for (const [seg, d] of Object.entries(DATA.segments)) {
        const pct = (d.ca / totalSegCA * 100).toFixed(1);
        tbody.innerHTML += `<tr><td><strong>${seg}</strong></td><td>${fmt(d.clients)}</td><td>${fmt(d.orders)}</td><td>${fmtMAD(d.ca)}</td><td>${fmtMAD(d.basket)}</td><td>${pct}%</td></tr>`;
    }
}

// ===== CHART CREATION =====
const charts = {};

function createCharts() {
    // --- Overview: CA mensuel ---
    charts.overviewCA = new Chart(document.getElementById('chart-overview-ca'), {
        type: 'line',
        data: {
            labels: MONTHS,
            datasets: [{
                label: '2026', data: DATA.ca2026,
                borderColor: COLORS.primary, backgroundColor: 'rgba(99,102,241,0.1)',
                fill: true, tension: 0.4, pointRadius: 4, pointHoverRadius: 7, borderWidth: 2.5,
            }, {
                label: '2025', data: DATA.ca2025,
                borderColor: COLORS.textColor, backgroundColor: 'transparent',
                borderDash: [6, 4], tension: 0.4, pointRadius: 0, borderWidth: 1.5,
            }]
        },
        options: { responsive: true, scales: { x: defaultScaleOpts, y: { ...defaultScaleOpts, ticks: { ...defaultScaleOpts.ticks, callback: v => fmt(v) } } }, plugins: { tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + fmtMAD(ctx.parsed.y) } } } }
    });

    // --- Overview: Catégories donut ---
    charts.overviewCat = new Chart(document.getElementById('chart-overview-cat'), {
        type: 'doughnut',
        data: {
            labels: CATEGORIES,
            datasets: [{ data: DATA.catCA, backgroundColor: [COLORS.primary, COLORS.gold, COLORS.green], borderWidth: 0, hoverOffset: 8 }]
        },
        options: { responsive: true, cutout: '65%', plugins: { tooltip: { callbacks: { label: ctx => ctx.label + ': ' + fmtMAD(ctx.parsed) } } } }
    });

    // --- Overview: Régions bar ---
    charts.overviewRegion = new Chart(document.getElementById('chart-overview-region'), {
        type: 'bar',
        data: {
            labels: REGIONS.map(r => r.length > 18 ? r.substring(0, 18) + '…' : r),
            datasets: [{ data: DATA.regionCA, backgroundColor: COLORS.palette, borderRadius: 6, borderSkipped: false }]
        },
        options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmtMAD(ctx.parsed.x) } } }, scales: { x: { ...defaultScaleOpts, ticks: { callback: v => fmt(v) } }, y: defaultScaleOpts } }
    });

    // --- Revenue: Comparaison N/N-1 ---
    charts.revenueCompare = new Chart(document.getElementById('chart-revenue-compare'), {
        type: 'bar',
        data: {
            labels: MONTHS,
            datasets: [
                { label: '2026', data: DATA.ca2026, backgroundColor: COLORS.primary, borderRadius: 6 },
                { label: '2025', data: DATA.ca2025, backgroundColor: 'rgba(148,163,184,0.3)', borderRadius: 6 },
            ]
        },
        options: { responsive: true, scales: { x: defaultScaleOpts, y: { ...defaultScaleOpts, ticks: { callback: v => fmt(v) } } }, plugins: { tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + fmtMAD(ctx.parsed.y) } } } }
    });

    // --- Revenue: Par région ---
    charts.revenueRegion = new Chart(document.getElementById('chart-revenue-region'), {
        type: 'bar',
        data: {
            labels: REGIONS.slice(0, 10).map(r => r.length > 20 ? r.substring(0, 20) + '…' : r),
            datasets: [{ data: DATA.regionCA, backgroundColor: COLORS.palette.map(c => c + 'cc'), borderRadius: 6 }]
        },
        options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmtMAD(ctx.parsed.y) } } }, scales: { x: defaultScaleOpts, y: { ...defaultScaleOpts, ticks: { callback: v => fmt(v) } } } }
    });

    // --- Products: Top 10 Tanger ---
    charts.topProducts = new Chart(document.getElementById('chart-top-products'), {
        type: 'bar',
        data: {
            labels: PRODUCTS_TANGER.map(p => p.name),
            datasets: [{ data: PRODUCTS_TANGER.map(p => p.ca), backgroundColor: COLORS.palette, borderRadius: 6, borderSkipped: false }]
        },
        options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmtMAD(ctx.parsed.x) } } }, scales: { x: { ...defaultScaleOpts, ticks: { callback: v => fmt(v) } }, y: defaultScaleOpts } }
    });

    // --- Products: Catégorie ---
    charts.catBreakdown = new Chart(document.getElementById('chart-cat-breakdown'), {
        type: 'doughnut',
        data: {
            labels: CATEGORIES,
            datasets: [{ data: DATA.catCA, backgroundColor: [COLORS.primary, COLORS.gold, COLORS.green], borderWidth: 0, hoverOffset: 8 }]
        },
        options: { responsive: true, cutout: '60%', plugins: { tooltip: { callbacks: { label: ctx => ctx.label + ': ' + fmtMAD(ctx.parsed) } } } }
    });

    // --- Products: Marques ---
    charts.brandBreakdown = new Chart(document.getElementById('chart-brand-breakdown'), {
        type: 'bar',
        data: {
            labels: BRANDS,
            datasets: [{ data: [22e6, 14e6, 9e6, 8e6, 6e6, 5e6, 4e6, 3e6], backgroundColor: COLORS.palette, borderRadius: 6 }]
        },
        options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmtMAD(ctx.parsed.y) } } }, scales: { x: defaultScaleOpts, y: { ...defaultScaleOpts, ticks: { callback: v => fmt(v) } } } }
    });

    // --- Segments: Donut CA ---
    const segLabels = Object.keys(DATA.segments);
    const segCA = segLabels.map(s => DATA.segments[s].ca);
    charts.segDonut = new Chart(document.getElementById('chart-seg-donut'), {
        type: 'doughnut',
        data: {
            labels: segLabels,
            datasets: [{ data: segCA, backgroundColor: [COLORS.gold, '#94a3b8', '#d97706'], borderWidth: 0, hoverOffset: 8 }]
        },
        options: { responsive: true, cutout: '65%', plugins: { tooltip: { callbacks: { label: ctx => ctx.label + ': ' + fmtMAD(ctx.parsed) } } } }
    });

    // --- Segments: Orders bar ---
    charts.segOrders = new Chart(document.getElementById('chart-seg-orders'), {
        type: 'bar',
        data: {
            labels: segLabels,
            datasets: [{ data: segLabels.map(s => DATA.segments[s].orders), backgroundColor: [COLORS.gold, '#94a3b8', '#d97706'], borderRadius: 8 }]
        },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: defaultScaleOpts, y: defaultScaleOpts } }
    });

    // --- Returns: Par catégorie ---
    const retCats = Object.keys(DATA.returns);
    const retVals = Object.values(DATA.returns);
    const retColors = retVals.map(v => v > 5 ? COLORS.red : v >= 3 ? COLORS.orange : COLORS.green);
    charts.returns = new Chart(document.getElementById('chart-returns'), {
        type: 'bar',
        data: {
            labels: retCats,
            datasets: [{ label: 'Taux de retour (%)', data: retVals, backgroundColor: retColors, borderRadius: 8 }]
        },
        options: {
            indexAxis: 'y', responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => ctx.parsed.x.toFixed(1) + '%' } },
                annotation: undefined
            },
            scales: { x: { ...defaultScaleOpts, max: 10, ticks: { callback: v => v + '%' } }, y: defaultScaleOpts }
        }
    });

    // --- Returns: Trend ---
    charts.returnsTrend = new Chart(document.getElementById('chart-returns-trend'), {
        type: 'line',
        data: {
            labels: MONTHS,
            datasets: [{
                label: 'Taux de retour global (%)', data: DATA.returnsTrend,
                borderColor: COLORS.orange, backgroundColor: 'rgba(249,115,22,0.1)',
                fill: true, tension: 0.4, pointRadius: 4, borderWidth: 2.5,
            }]
        },
        options: { responsive: true, scales: { x: defaultScaleOpts, y: { ...defaultScaleOpts, ticks: { callback: v => v.toFixed(1) + '%' } } } }
    });

    // --- Ramadan: Trend with highlighted zones ---
    const ramTrend = MONTHS.map((_, i) => {
        const base = 1500000;
        const isMar = (i === 2 || i === 3); // Ramadan months approx
        return Math.round(base * (isMar ? 1.5 : 1) * (1 + (Math.random() - 0.5) * 0.2));
    });
    charts.ramadanTrend = new Chart(document.getElementById('chart-ramadan-trend'), {
        type: 'line',
        data: {
            labels: MONTHS,
            datasets: [{
                label: 'Alimentation CA', data: ramTrend,
                borderColor: COLORS.green, backgroundColor: 'rgba(16,185,129,0.1)',
                fill: true, tension: 0.4, pointRadius: 5, borderWidth: 2.5,
                pointBackgroundColor: MONTHS.map((_, i) => (i === 2 || i === 3) ? COLORS.gold : COLORS.green),
                pointBorderColor: MONTHS.map((_, i) => (i === 2 || i === 3) ? COLORS.gold : COLORS.green),
                pointRadius: MONTHS.map((_, i) => (i === 2 || i === 3) ? 8 : 4),
            }]
        },
        options: { responsive: true, scales: { x: defaultScaleOpts, y: { ...defaultScaleOpts, ticks: { callback: v => fmt(v) } } }, plugins: { tooltip: { callbacks: { label: ctx => { const isR = (ctx.dataIndex === 2 || ctx.dataIndex === 3); return (isR ? '🌙 Ramadan — ' : '') + fmtMAD(ctx.parsed.y); } } } } }
    });

    // --- Ramadan: Compare ---
    charts.ramadanCompare = new Chart(document.getElementById('chart-ramadan-compare'), {
        type: 'bar',
        data: {
            labels: CATEGORIES,
            datasets: [
                { label: 'Pendant Ramadan', data: [6200000, 4800000, 4200000], backgroundColor: COLORS.gold, borderRadius: 6 },
                { label: 'Hors Ramadan (moy)', data: [5800000, 4500000, 2800000], backgroundColor: 'rgba(148,163,184,0.4)', borderRadius: 6 },
            ]
        },
        options: { responsive: true, scales: { x: defaultScaleOpts, y: { ...defaultScaleOpts, ticks: { callback: v => fmt(v) } } }, plugins: { tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + fmtMAD(ctx.parsed.y) } } } }
    });
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    updateKPIs();
    createCharts();
});
