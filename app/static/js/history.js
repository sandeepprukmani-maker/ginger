document.addEventListener('DOMContentLoaded', () => {
    const deleteAllBtn = document.getElementById('delete-all-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    
    if (deleteAllBtn) {
        deleteAllBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete all history?')) {
                console.log('Deleting all history...');
            }
        });
    }
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('Refreshing history...');
            location.reload();
        });
    }
});
