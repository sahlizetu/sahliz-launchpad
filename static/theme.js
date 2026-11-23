(() => {
    const storageKey = 'sahliz-theme';
    const root = document.documentElement;

    try {
        root.dataset.theme = localStorage.getItem(storageKey) === 'dark' ? 'dark' : 'light';
    } catch {
        root.dataset.theme = 'light';
    }

    document.addEventListener('DOMContentLoaded', () => {
        const toggle = document.getElementById('theme-toggle');
        const browserTheme = document.querySelector('meta[name="theme-color"]');
        const applyTheme = dark => {
            root.dataset.theme = dark ? 'dark' : 'light';
            toggle.setAttribute('aria-pressed', String(dark));
            browserTheme.content = dark ? '#101d2e' : '#ffffff';
        };
        applyTheme(root.dataset.theme === 'dark');
        toggle.addEventListener('click', () => {
            applyTheme(root.dataset.theme !== 'dark');
            try {
                localStorage.setItem(storageKey, root.dataset.theme);
            } catch {
                // The current page still uses the selected theme.
            }
        });

        const menus = document.querySelectorAll('.header-menu');
        document.addEventListener('click', event => {
            for (const menu of menus) {
                if (!menu.contains(event.target)) menu.open = false;
            }
        });
        document.addEventListener('keydown', event => {
            if (event.key !== 'Escape') return;
            for (const menu of menus) {
                if (!menu.open) continue;
                menu.open = false;
                menu.querySelector('summary').focus();
            }
        });
    });
})();
