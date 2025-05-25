import { writable } from 'svelte/store';
import { browser } from '$app/environment';

function createThemeStore() {
  const { subscribe, set, update } = writable({
    isDark: false,
    initialized: false
  });

  return {
    subscribe,
    
    initialize() {
      if (!browser) return;
      
      // Check for saved theme preference or default to system preference
      const savedTheme = localStorage.getItem('homegrow-theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      
      const isDark = savedTheme ? savedTheme === 'dark' : prefersDark;
      
      this.setTheme(isDark);
      
      // Listen for system theme changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('homegrow-theme')) {
          this.setTheme(e.matches);
        }
      });
      
      update(state => ({ ...state, initialized: true }));
    },
    
    setTheme(isDark) {
      if (!browser) return;
      
      update(state => ({ ...state, isDark }));
      
      // Update DOM
      if (isDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      // Save preference
      localStorage.setItem('homegrow-theme', isDark ? 'dark' : 'light');
    },
    
    toggle() {
      update(state => {
        const newIsDark = !state.isDark;
        this.setTheme(newIsDark);
        return { ...state, isDark: newIsDark };
      });
    }
  };
}

export const themeStore = createThemeStore(); 