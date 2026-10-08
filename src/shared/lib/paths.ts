import type { Language } from '../content/i18n';

export const withBase = (path = '') => `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`;
export const localizedPath = (path: string, lang: Language) => withBase(`${lang === 'en' ? 'en/' : ''}${path}`);
