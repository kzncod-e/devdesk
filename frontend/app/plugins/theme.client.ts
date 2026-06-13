// Apply the persisted theme as early as possible to avoid a flash of the wrong palette.
export default defineNuxtPlugin(() => {
  useTheme().init();
});
