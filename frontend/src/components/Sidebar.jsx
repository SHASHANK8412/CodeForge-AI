function Sidebar() {
    return (
        <div className="w-64 bg-[#202123] p-4 flex flex-col">

            <button
                className="
                    border
                    border-gray-600
                    rounded-lg
                    p-3
                    hover:bg-gray-700
                    transition
                "
            >
                + New Chat
            </button>

            <div className="mt-6 text-gray-400">

                History

            </div>

        </div>
    );
}

export default Sidebar;