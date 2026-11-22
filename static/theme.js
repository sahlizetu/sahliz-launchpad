const themeStorageKey = 'sahliz-theme';
const root = document.documentElement;

try {
    root.dataset.theme = localStorage.getItem(themeStorageKey) === 'dark' ? 'dark' : 'light';
} catch {
    root.dataset.theme = 'light';
}

document.addEventListener('DOMContentLoaded', () => {
    const picker = document.getElementById('theme-picker');
    const browserTheme = document.querySelector('meta[name="theme-color"]');
    const applyTheme = theme => {
        root.dataset.theme = theme;
        browserTheme.content = theme === 'dark' ? '#101b19' : '#133b34';
    };
    picker.value = root.dataset.theme;
    applyTheme(picker.value);
    picker.addEventListener('change', () => {
        applyTheme(picker.value);
        try {
            localStorage.setItem(themeStorageKey, picker.value);
        } catch {
            // The theme still applies to the current page.
        }
    });
});
