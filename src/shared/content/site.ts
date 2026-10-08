export const navigation = [
  { path: '', key: 'home' },
  { path: 'members/', key: 'faculty' },
  { path: 'team/', key: 'team' },
] as const;

export const laboratory = {
  name: 'IRSL 實驗室',
  phone: '07-3814526 #15675',
  phoneHref: 'tel:073814526;ext=15675',
  address: '807 高雄市三民區寶珠里建工路 415 號',
};

export const mapQuery = encodeURIComponent(laboratory.address);

export const addressEn = 'No. 415, Jiangong Rd., Baozhu Village, Sanmin District, Kaohsiung City 807';
