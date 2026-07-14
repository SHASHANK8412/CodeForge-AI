function RagUploadPanel({
    documentMode,
    selectedFiles,
    onFileChange,
    onToggleDocumentMode,
    uploadProgress,
    uploading,
    status,
    error,
    inputRef,
}) {
    if (!documentMode) {
        return null;
    }

    return (
        <div className="px-6 py-4 border-b border-gray-700 space-y-3 bg-[#262730] rounded-2xl mx-6 mt-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <div className="text-lg font-semibold text-white">Upload Knowledge Base</div>
                    <div className="text-sm text-gray-300">Select one or more PDFs, then ask questions against the indexed content.</div>
                </div>

                <input
                    ref={inputRef}
                    type="file"
                    multiple
                    accept=".pdf,.txt,.md"
                    onChange={onFileChange}
                    className="text-sm text-gray-300"
                />
            </div>

            {selectedFiles.length > 0 && (
                <div className="text-sm text-amber-300">
                    Selected: {selectedFiles.map((file) => file.name).join(", ")}
                </div>
            )}

            {uploading && (
                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div
                        className="h-2 bg-amber-400 transition-all"
                        style={{ width: `${uploadProgress}%` }}
                    />
                </div>
            )}

            {status && (
                <div className="text-sm text-green-300">{status}</div>
            )}

            {error && (
                <div className="text-sm text-red-300">{error}</div>
            )}

            <button
                onClick={onToggleDocumentMode}
                className="text-sm text-gray-400 hover:text-white transition"
            >
                Exit document mode
            </button>
        </div>
    );
}

export default RagUploadPanel;