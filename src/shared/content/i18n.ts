import { laboratory } from './site';

export type Language = 'zh-Hant' | 'en';

export const ui = {
  'zh-Hant': {
    labName: laboratory.name, brand: '實驗室', homeLabel: 'IRSL 實驗室首頁',
    home: '首頁', faculty: '教師介紹', team: '實驗室成員',
    navigation: '主要導覽', openMenu: '開啟選單 ＋', closeMenu: '關閉選單 −',
    language: '語言', skip: '跳至主要內容', phone: '電話', address: '地址',
    location: '實驗室位置', openMap: '在 Google 地圖開啟',
    homeDescription: 'IRSL 實驗室的建築節能、室內環境、智慧感測、BIM、資源最佳化與都市氣候研究。',
    facultyDescription: '許協誌老師的基本資料、學經歷、期刊與研討會論文、專利與教學課程。',
    teamDescription: 'IRSL 實驗室博士生與碩士生成員名錄。',
  },
  en: {
    labName: 'IRSL Laboratory', brand: 'Laboratory', homeLabel: 'IRSL Laboratory home',
    home: 'Home', faculty: 'Faculty', team: 'Lab Members',
    navigation: 'Main navigation', openMenu: 'Open menu ＋', closeMenu: 'Close menu −',
    language: 'Language', skip: 'Skip to main content', phone: 'Phone', address: 'Address',
    location: 'Lab location', openMap: 'Open in Google Maps',
    homeDescription: 'IRSL Laboratory research on building energy efficiency, indoor environments, smart sensing, BIM, resource optimization and urban climate.',
    facultyDescription: 'Hsieh-Chih Hsu’s profile, education, experience, journal and conference papers, patents and courses.',
    teamDescription: 'Doctoral and master’s students at IRSL Laboratory.',
  },
};
