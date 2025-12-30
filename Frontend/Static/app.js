/* ================= GLOBAL STATE ================= */
const forensicHistory = {}; 
let currentAnalysisData = null; 

/* ================= FORENSIC DEFINITIONS ================= */
const forensicDefinitions = {
    "beneish": "Beneish M-Score: A mathematical model using 8 financial ratios to identify if a company has manipulated its earnings. A score > -1.78 suggests a high probability of manipulation.",
    "accruals": "Accruals Gap: Measures the difference between reported net income and actual operating cash flow. High positive accruals often signal aggressive non-cash earnings recognition.",
    "tax": "Tax Gap: The discrepancy between book tax (reported) and cash tax (paid). Significant gaps can indicate that paper profits are not supported by real taxable events.",
    "debt": "Debt Stress: Evaluates total borrowings against asset quality. Excessive leverage increases the management's incentive to window-dress financial statements.",
    "cash": "Cash Quality: Percentage of revenue converted into operating cash. Values below 70% suggest that sales may not be resulting in actual cash collection."
};

/* ================= NAVIGATION ================= */
/**
 * Handles switching between Dashboard, Data Explorer, Forensic AI, and Settings tabs
 */
function showTab(tabId, el) {
    document.querySelectorAll(".tab").forEach(tab => tab.classList.add("hidden"));
    document.getElementById(tabId).classList.remove("hidden");
    
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("bg-blue-600/10", "text-blue-400", "font-semibold", "active-nav");
        item.classList.add("text-slate-400");
    });
    el.classList.add("bg-blue-600/10", "text-blue-400", "font-semibold", "active-nav");
}

function toggleSidebar() { 
    document.getElementById("sidebar").classList.toggle("collapsed"); 
}

function openHelpModal() { document.getElementById("helpModal").classList.remove("hidden"); }
function closeHelpModal() { document.getElementById("helpModal").classList.add("hidden"); }

/* ================= AI WORKSPACE LOGIC ================= */
function quickPrompt(text) {
    const input = document.getElementById("chatInput");
    if(input) {
        input.value = text;
        handleChat(text);
        input.value = "";
    }
}

document.getElementById("chatInput")?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        handleChat(e.target.value);
        e.target.value = "";
    }
});

function handleChat(query) {
    appendMessage("User", query);
    setTimeout(() => {
        let response = "Please upload an Excel workbook to begin the forensic audit.";
        if (currentAnalysisData) {
            const q = query.toLowerCase();
            if (q.includes("risk")) {
                response = `Based on current data for ${currentAnalysisData.name}, the manipulation signal is ${currentAnalysisData.earnings_manipulation_signal}. The Beneish M-Score stands at ${currentAnalysisData.beneish_m_score}.`;
            } else if (q.includes("accruals")) {
                response = `The Accruals Gap is ${currentAnalysisData.accruals_gap}%. Typically, values over 25% indicate aggressive accounting.`;
            } else if (q.includes("tax")) {
                response = `The Tax Gap is ${currentAnalysisData.tax_gap}%. This checks if provisioned tax (${currentAnalysisData.tax_paid.toLocaleString()}) aligns with reported profits.`;
            } else {
                response = `Regarding ${currentAnalysisData.name}, we see a Debt Stress of ${currentAnalysisData.debt_asset_stress}% and Cash Quality of ${currentAnalysisData.cash_quality}%. Which would you like to deep-dive into?`;
            }
        }
        appendMessage("AI Auditor", response);
    }, 600);
}

function appendMessage(sender, text) {
    const chatBody = document.getElementById("chatBody");
    const isAi = sender === "AI Auditor";
    
    if (chatBody) {
        const msg = document.createElement("div");
        msg.className = isAi 
            ? "max-w-2xl bg-white p-6 rounded-2xl border border-slate-200 shadow-sm" 
            : "max-w-xl ml-auto bg-blue-600 text-white p-6 rounded-2xl shadow-md";
        msg.innerHTML = `
            <span class="font-bold text-[9px] block uppercase mb-1 ${isAi ? 'text-blue-600' : 'text-blue-100'}">${sender}</span>
            <span class="text-sm leading-relaxed">${text}</span>
        `;
        chatBody.appendChild(msg);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
}

/* ================= ANALYSIS & PDF EXPORT ================= */
function runAnalysis() {
    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) return alert("Select a financial workbook.");
    
    document.getElementById("loadingText").classList.remove("hidden");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch("/analyze", { method: "POST", body: formData })
    .then(res => res.json())
    .then(data => {
        document.getElementById("loadingText").classList.add("hidden");
        if (data.error) throw new Error(data.error);
        renderAll(data);
    })
    .catch(err => alert(err.message));
}

function exportPDF() {
    if (!currentAnalysisData) return;
    fetch("/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentAnalysisData)
    })
    .then(res => {
        if (!res.ok) throw new Error("Failed to generate PDF");
        return res.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Forensic_Report_${currentAnalysisData.name}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(err => alert(err.message));
}

/* ================= RENDERING ENGINE ================= */
function renderAll(data) {
    currentAnalysisData = data;
    renderMetrics(data);
    renderBenford(data.benford);
    renderExplorer(data);
    renderFlags(data);
    renderVerdict(data);
    
    const exportBtn = document.getElementById("exportBtn");
    if(exportBtn) exportBtn.disabled = false;
    
    const statusBadge = document.getElementById("statusBadge");
    if(statusBadge) statusBadge.innerText = "ANALYSIS COMPLETE";
    
    addToHistory(data.name, data);
}

function renderMetrics(data) {
    const metricsDiv = document.getElementById("metrics");
    if (!metricsDiv) return;
    metricsDiv.innerHTML = "";
    
    const config = [
        ["Beneish M-Score", data.beneish_m_score, "beneish"],
        ["Accruals Gap (%)", data.accruals_gap, "accruals"],
        ["Tax Gap (%)", data.tax_gap, "tax"],
        ["Debt Stress (%)", data.debt_asset_stress, "debt"],
        ["Cash Quality (%)", data.cash_quality, "cash"]
    ];

    config.forEach(([label, value, type]) => {
        const severity = getSeverityColor(type, value);
        const card = document.createElement("div");
        card.className = "group relative bg-white p-5 rounded-2xl border border-slate-200 hover:border-blue-400 hover:shadow-md transition-all cursor-help";
        card.innerHTML = `
            <div class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">${label}</div>
            <div class="text-2xl font-black mt-1 ${severity}">${value ?? 'N/A'}</div>
            <div class="absolute bottom-full left-0 mb-3 w-64 bg-slate-900 text-white text-[10px] p-3 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-2xl leading-relaxed">
                <span class="text-blue-400 font-bold block mb-1">Audit Description:</span>
                ${forensicDefinitions[type]}
            </div>
        `;
        metricsDiv.appendChild(card);
    });
}

function getSeverityColor(type, value) {
    if (value === null || isNaN(value)) return "text-slate-300";
    const isBad = (type === "beneish" && value > -1.78) || 
                  (type === "accruals" && value > 25) || 
                  (type === "tax" && value > 10);
    return isBad ? "text-rose-500" : "text-emerald-500";
}

function renderExplorer(data) {
    const table = document.getElementById("rawDataTable");
    if (!table) return;
    const rows = [
        ["Reported Revenue", data.revenue || 0],
        ["Total Assets", data.total_assets || 0],
        ["Operating Cash Flow", data.ocf || 0],
        ["Trade Receivables", data.receivables || 0],
        ["Total Borrowings", data.borrowings || 0],
        ["Tax Provision", data.tax_paid || 0],
        ["Profit Before Tax", data.pbt || 0]
    ];
    
    table.innerHTML = rows.map(r => `
        <tr class="hover:bg-slate-50 transition">
            <td class="p-4 font-semibold text-slate-700">${r[0]}</td>
            <td class="p-4 text-slate-500 font-mono">${r[1].toLocaleString()}</td>
        </tr>
    `).join("");
    
    Plotly.newPlot("explorerChart", [{
        x: rows.map(r => r[0]),
        y: rows.map(r => r[1]),
        type: 'bar',
        marker: { color: '#3b82f6', borderRadius: 8 }
    }], { 
        margin: { t: 20, b: 40, l: 60, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { family: 'Inter', size: 11, color: '#64748b' }
    }, { responsive: true });
}

function renderBenford(benford) {
    Plotly.newPlot("benfordChart", [
        { x: [1,2,3,4,5,6,7,8,9], y: benford.actual, type: "bar", name: "Actual", marker: {color: '#3b82f6'} },
        { x: [1,2,3,4,5,6,7,8,9], y: benford.theoretical, type: "scatter", mode: "lines+markers", name: "Theoretical", line: {color: '#f43f5e'} }
    ], { 
        margin: { t: 10, b: 30, l: 40, r: 10 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { family: 'Inter', size: 10, color: '#64748b' },
        legend: { orientation: "h", y: -0.2 }
    }, { responsive: true });
}

function renderFlags(data) {
    const tbody = document.getElementById("flagsTable");
    if (!tbody) return;
    tbody.innerHTML = "";
    const flags = [
        ["Beneish M-Score", data.beneish_m_score, data.beneish_m_score > -1.78],
        ["Accruals Gap", `${data.accruals_gap}%`, data.accruals_gap > 25],
        ["Tax Gap", `${data.tax_gap}%`, data.tax_gap > 10],
        ["Debt Stress", `${data.debt_asset_stress}%`, data.debt_asset_stress > 50]
    ];
    flags.forEach(([m, v, high]) => {
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50 transition border-b border-slate-50">
                <td class="p-4 font-medium text-slate-700">${m}</td>
                <td class="p-4 text-slate-500 font-mono">${v}</td>
                <td class="p-4 font-bold ${high ? 'text-rose-500' : 'text-emerald-500'}">${high ? 'CRITICAL' : 'OPTIMAL'}</td>
            </tr>`;
    });
}

function renderVerdict(data) {
    const box = document.getElementById("finalVerdict");
    if (!box) return;
    const isHigh = data.earnings_manipulation_signal === "HIGH";
    box.innerText = isHigh ? "⚠️ HIGH RISK DETECTED" : "✅ LOW RISK DETECTED";
    box.className = `p-10 rounded-[2.5rem] border-2 font-black text-2xl transition-all shadow-lg ${
        isHigh ? 'bg-rose-50 border-rose-200 text-rose-600 shadow-rose-100' : 'bg-emerald-50 border-emerald-200 text-emerald-600 shadow-emerald-100'
    }`;
}

function addToHistory(name, data) {
    const list = document.getElementById("historyList");
    if(!list) return;
    if (list.innerText.includes("No recent")) list.innerHTML = "";
    const entryId = "entry_" + Date.now();
    forensicHistory[entryId] = data;
    const li = document.createElement("li");
    li.className = "p-2 rounded-xl hover:bg-slate-800 transition cursor-pointer flex justify-between items-center";
    li.innerHTML = `
        <span class="truncate pr-2">${name}</span> 
        <small class="font-bold px-2 py-0.5 rounded border ${
            data.earnings_manipulation_signal === 'HIGH' ? 'border-rose-500 text-rose-500' : 'border-emerald-500 text-emerald-500'
        }">${data.earnings_manipulation_signal}</small>
    `;
    li.onclick = () => renderAll(forensicHistory[entryId]);
    list.prepend(li);
}

/* ================= SIMULATION & ONLOAD ================= */
window.onload = () => {
    const sim = { 
        name: "ASIAN PAINTS LTD", 
        beneish_m_score: -2.54, 
        accruals_gap: 12.4, 
        tax_gap: 4.2, 
        debt_asset_stress: 18.1, 
        cash_quality: 92.4, 
        earnings_manipulation_signal: "LOW", 
        revenue: 345000000, 
        total_assets: 1200000000, 
        ocf: 85000000, 
        receivables: 42000000, 
        borrowings: 217000000,
        tax_paid: 4500000,
        pbt: 107000000,
        benford: { 
            actual: [30.5, 17.2, 12.1, 9.4, 8.1, 6.5, 5.9, 5.2, 5.1], 
            theoretical: [30.1, 17.6, 12.5, 9.7, 7.9, 6.7, 5.8, 5.1, 4.6] 
        } 
    };
    renderAll(sim);
};

const exportBtn = document.getElementById("exportBtn");
if(exportBtn) exportBtn.onclick = exportPDF;