export class LocalStorageManager {
    static saveStatsToLocalStorage(properties, type) {
        localStorage.setItem('currentStats', JSON.stringify({
            properties,
            type,
            timestamp: Date.now()
        }));
    }

    static clearStatsFromLocalStorage() {
        localStorage.removeItem('currentStats');
    }

    clearStatistics() {
        const statsDiv = document.getElementById('attributes');
        const clearButton = document.getElementById('clearStats');

        statsDiv.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                No feature selected
            </div>
        `;
        clearButton.classList.add('hidden');

        LocalStorageManager.clearStatsFromLocalStorage();
    }
}