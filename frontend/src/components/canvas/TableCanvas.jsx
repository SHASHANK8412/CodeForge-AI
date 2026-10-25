import React from "react";
import { FaPlus, FaTrash, FaMagic, FaSortAmountDown } from "react-icons/fa";

export default function TableCanvas({ 
  content = { columns: [], rows: [] }, 
  onChange, 
  onAiTransform, 
  isReadOnly = false 
}) {
  const columns = content?.columns || ["Item", "Feature", "Status"];
  const rows = content?.rows || [["Item 1", "Active", "Verified"]];

  const handleCellChange = (rIdx, cIdx, val) => {
    const newRows = rows.map((r, i) => i === rIdx ? r.map((c, j) => j === cIdx ? val : c) : r);
    if (onChange) onChange({ ...content, rows: newRows });
  };

  const handleColumnHeaderChange = (cIdx, val) => {
    const newCols = columns.map((c, i) => i === cIdx ? val : c);
    if (onChange) onChange({ ...content, columns: newCols });
  };

  const handleAddRow = () => {
    const emptyRow = Array(columns.length).fill("New Data");
    if (onChange) onChange({ ...content, rows: [...rows, emptyRow] });
  };

  const handleAddColumn = () => {
    const colName = prompt("Enter new column name (e.g. Pricing, Security Score):");
    if (!colName || !colName.trim()) return;
    const newCols = [...columns, colName.trim()];
    const newRows = rows.map(r => [...r, "TBD"]);
    if (onChange) onChange({ columns: newCols, rows: newRows });
  };

  const handleDeleteRow = (rIdx) => {
    const newRows = rows.filter((_, i) => i !== rIdx);
    if (onChange) onChange({ ...content, rows: newRows });
  };

  return (
    <div className="h-full flex flex-col p-6 space-y-4 font-sans text-xs">
      {/* Table Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#242833]">
        <div>
          <h2 className="text-sm font-bold text-white">Structured Data & Comparison Matrix</h2>
          <span className="text-[10px] text-[#64748B] font-mono">
            {rows.length} Rows • {columns.length} Columns
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onAiTransform("Add a detailed Pricing & License column with current market tiers")}
            className="px-2.5 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-emerald-300 rounded-xl font-semibold transition border border-[#242833] cursor-pointer"
          >
            💰 Add Pricing Column
          </button>

          <button
            onClick={() => onAiTransform("Sort matrix by Performance & Developer Ecosystem")}
            className="px-2.5 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-indigo-300 rounded-xl font-semibold transition border border-[#242833] cursor-pointer"
          >
            📊 Sort by Metric
          </button>

          <button
            onClick={handleAddColumn}
            className="px-3 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-gray-300 rounded-xl font-semibold transition border border-[#242833] cursor-pointer"
          >
            + Column
          </button>

          <button
            onClick={handleAddRow}
            className="px-3 py-1.5 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl font-bold transition shadow cursor-pointer"
          >
            + Row
          </button>
        </div>
      </div>

      {/* Spreadsheet Matrix Grid */}
      <div className="flex-1 overflow-auto rounded-2xl border border-[#242833] bg-[#0F1117] custom-scrollbar">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#151821] border-b border-[#242833] text-[11px] font-mono text-indigo-300 uppercase">
              {columns.map((col, cIdx) => (
                <th key={cIdx} className="p-3 border-r border-[#242833] font-bold">
                  <input
                    type="text"
                    value={col}
                    onChange={(e) => handleColumnHeaderChange(cIdx, e.target.value)}
                    disabled={isReadOnly}
                    className="bg-transparent font-bold text-indigo-300 outline-none w-full"
                  />
                </th>
              ))}
              <th className="w-10 p-3 text-center"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1C202B]">
            {rows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-[#151821]/60 transition">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="p-2.5 border-r border-[#1C202B]">
                    <input
                      type="text"
                      value={cell || ""}
                      onChange={(e) => handleCellChange(rIdx, cIdx, e.target.value)}
                      disabled={isReadOnly}
                      className="bg-transparent text-gray-200 text-xs outline-none w-full p-1 rounded focus:bg-[#08090D] focus:ring-1 focus:ring-indigo-500"
                    />
                  </td>
                ))}
                <td className="p-2.5 text-center">
                  <button
                    onClick={() => handleDeleteRow(rIdx)}
                    className="text-gray-600 hover:text-rose-400 p-1"
                    title="Delete row"
                  >
                    <FaTrash size={10} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
