import type { ImageMetadata } from 'astro';
interface Member { name: string; photo: ImageMetadata | null; alt: string; altEn?: string }

// Import local photos from ../assets/; Astro emits BASE_PATH-aware image URLs.
// Replace name, photo and alt together when confirmed member information is available.
export const memberGroups: { id: string; title: string; titleEn: string; label: string; members: Member[] }[] = [
  { id: 'doctoral', title: '博士生', titleEn: 'Doctoral students', label: 'DOCTORAL STUDENTS', members: [
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
  ] },
  { id: 'masters', title: '碩士生', titleEn: 'Master’s students', label: 'MASTER’S STUDENTS', members: [
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
    { name: '', photo: null, alt: '成員頭像', altEn: 'Member portrait' },
  ] },
];
