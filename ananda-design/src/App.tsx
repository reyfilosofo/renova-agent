import { useEffect, useMemo, useRef, useState } from 'react';
import { api, auth } from '@appdeploy/client';
import {
  Moon,
  Sun,
  LogIn,
  LogOut,
  Sparkles,
  Download,
  FileArchive,
  Save,
  ShieldCheck,
  Check,
  UserRound,
  BookOpen,
  Baby,
  Users,
  Leaf,
  Compass,
  LoaderCircle,
} from 'lucide-react';
import JSZip from 'jszip';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

type Locale = 'es' | 'en' | 'de' | 'zh' | 'ru' | 'ar';
type Edition = 'seed' | 'core' | 'signature' | 'child' | 'duo';
type Chart = {
  name: string;
  birthDate: string;
  birthTime: string;
  birthPlace: string;
  timezone: string;
  type: string;
  strategy: string;
  authority: string;
  profile: string;
  definition: string;
  signature: string;
  notSelf: string;
  incarnationCross: string;
  definedCenters: string[];
  openCenters: string[];
  channels: string[];
  gates: number[];
  source?: string;
};
type Reading = {
  title: string;
  subtitle: string;
  opening: string;
  sections: { heading: string; body: string; practice?: string }[];
  closing: string;
};

const C: Record<Locale, Record<string, string>> = {
  es: {
    create: 'Crear carta',
    method: 'Método',
    editions: 'Ediciones',
    library: 'Biblioteca',
    login: 'Acceder',
    logout: 'Salir',
    eyebrow: 'ANANDA COMUNIDAD · by Sara Garcini',
    hero: 'Tu diseño, convertido en un objeto de vida.',
    lead: 'Calcula, valida, interpreta y edita una carta de Human Design con precisión estructural y una dirección de arte concebida para conservarse.',
    cta: 'Crear mi mapa',
    sample: 'Ver edición Regina',
    calc: 'Calcular carta',
    calculating: 'Calculando…',
    name: 'Nombre completo',
    date: 'Fecha de nacimiento',
    time: 'Hora exacta',
    place: 'Lugar de nacimiento',
    zone: 'Zona horaria IANA',
    focus: '¿Qué quieres comprender mejor?',
    child: 'Lectura infantil / crianza',
    generate: 'Generar lectura afinada',
    generating: 'Afinando…',
    pdf: 'Descargar PDF',
    zip: 'Descargar ZIP',
    save: 'Guardar',
    buy: 'Comprar',
    pending: 'Pago seguro pendiente de configuración',
    methodTitle: 'Criterio editorial',
    methodBody:
      'ANANDA separa la mecánica de la interpretación. Tipo, Estrategia, Autoridad, Perfil, Definición, Centros, Canales y Cruz se validan primero; después se convierten en una lectura humana, profunda y no determinista.',
    ep: 'Human Design se presenta aquí como marco simbólico e interpretativo de autoconocimiento, no como instrumento clínico ni ciencia empírica validada.',
    products: 'Ediciones personales',
    lib: 'Mi biblioteca',
    empty: 'Aún no hay cartas guardadas.',
    provider: 'Motor de cálculo',
    connected: 'Conectado',
    waiting: 'Pendiente',
    deep: 'Lectura profunda',
    import: 'Importar JSON validado',
    invalid: 'Completa nombre, fecha, hora, lugar y zona horaria.',
    api: 'Para cálculo real en tiempo real falta conectar la clave segura del proveedor. El ejemplo Regina y la importación validada ya funcionan.',
    saved: 'Guardado en tu biblioteca.',
    readerr: 'No fue posible generar la lectura. Intenta de nuevo.',
    calcerr:
      'No fue posible calcular la carta. Revisa los datos o la configuración.',
    subtitle: 'Human Design · Personal Maps',
    disclaimer: 'Un mapa para observarte, no una etiqueta para encerrarte.',
  },
  en: {
    create: 'Create chart',
    method: 'Method',
    editions: 'Editions',
    library: 'Library',
    login: 'Sign in',
    logout: 'Sign out',
    eyebrow: 'ANANDA COMUNIDAD · by Sara Garcini',
    hero: 'Your design, turned into a life object.',
    lead: 'Calculate, validate, interpret and edit a Human Design chart with structural precision and art direction designed to be kept.',
    cta: 'Create my map',
    sample: 'View Regina edition',
    calc: 'Calculate chart',
    calculating: 'Calculating…',
    name: 'Full name',
    date: 'Birth date',
    time: 'Exact time',
    place: 'Birth place',
    zone: 'IANA timezone',
    focus: 'What would you like to understand better?',
    child: 'Child / parenting reading',
    generate: 'Generate refined reading',
    generating: 'Refining…',
    pdf: 'Download PDF',
    zip: 'Download ZIP',
    save: 'Save',
    buy: 'Buy',
    pending: 'Secure payment is awaiting configuration',
    methodTitle: 'Editorial method',
    methodBody:
      'ANANDA separates mechanics from interpretation. Type, Strategy, Authority, Profile, Definition, Centers, Channels and Cross are validated first; only then are they translated into a deep, humane, non-deterministic reading.',
    ep: 'Human Design is presented here as a symbolic and interpretive self-knowledge framework, not as a clinical instrument or empirically validated science.',
    products: 'Personal editions',
    lib: 'My library',
    empty: 'No saved charts yet.',
    provider: 'Calculation engine',
    connected: 'Connected',
    waiting: 'Pending',
    deep: 'Deep reading',
    import: 'Import validated JSON',
    invalid: 'Complete name, date, time, place and timezone.',
    api: 'Real-time calculation needs the secure provider key. The Regina example and validated JSON import already work.',
    saved: 'Saved to your library.',
    readerr: 'The reading could not be generated. Try again.',
    calcerr:
      'The chart could not be calculated. Check the data or configuration.',
    subtitle: 'Human Design · Personal Maps',
    disclaimer: 'A map to observe yourself, not a label to confine you.',
  },
  de: {
    create: 'Chart erstellen',
    method: 'Methode',
    editions: 'Editionen',
    library: 'Bibliothek',
    login: 'Anmelden',
    logout: 'Abmelden',
    eyebrow: 'ANANDA COMUNIDAD · by Sara Garcini',
    hero: 'Dein Design als Lebensobjekt.',
    lead: 'Berechne, validiere, interpretiere und editiere Human Design mit struktureller Präzision und einer Gestaltung zum Bewahren.',
    cta: 'Meine Karte erstellen',
    sample: 'Regina-Edition ansehen',
    calc: 'Chart berechnen',
    calculating: 'Berechnung…',
    name: 'Vollständiger Name',
    date: 'Geburtsdatum',
    time: 'Genaue Uhrzeit',
    place: 'Geburtsort',
    zone: 'IANA-Zeitzone',
    focus: 'Was möchtest du besser verstehen?',
    child: 'Kinder-/Eltern-Lesung',
    generate: 'Verfeinerte Lesung erzeugen',
    generating: 'Verfeinerung…',
    pdf: 'PDF herunterladen',
    zip: 'ZIP herunterladen',
    save: 'Speichern',
    buy: 'Kaufen',
    pending: 'Sichere Zahlung wartet auf Konfiguration',
    methodTitle: 'Redaktionelle Methode',
    methodBody:
      'ANANDA trennt Mechanik und Interpretation. Typ, Strategie, Autorität, Profil, Definition, Zentren, Kanäle und Kreuz werden zuerst validiert und erst danach in eine tiefe, nicht-deterministische Lesung übersetzt.',
    ep: 'Human Design wird hier als symbolisch-interpretativer Rahmen zur Selbsterkenntnis dargestellt, nicht als klinisches Instrument oder empirisch validierte Wissenschaft.',
    products: 'Persönliche Editionen',
    lib: 'Meine Bibliothek',
    empty: 'Noch keine gespeicherten Charts.',
    provider: 'Berechnungsmotor',
    connected: 'Verbunden',
    waiting: 'Ausstehend',
    deep: 'Vertiefte Lesung',
    import: 'Validiertes JSON importieren',
    invalid: 'Name, Datum, Uhrzeit, Ort und Zeitzone vervollständigen.',
    api: 'Für Echtzeitberechnung fehlt noch der sichere Provider-Schlüssel. Regina-Beispiel und validierter JSON-Import funktionieren bereits.',
    saved: 'In deiner Bibliothek gespeichert.',
    readerr: 'Lesung konnte nicht erzeugt werden.',
    calcerr: 'Chart konnte nicht berechnet werden.',
    subtitle: 'Human Design · Personal Maps',
    disclaimer: 'Eine Karte zum Beobachten, kein Etikett zum Einsperren.',
  },
  zh: {
    create: '生成图谱',
    method: '方法',
    editions: '版本',
    library: '档案',
    login: '登录',
    logout: '退出',
    eyebrow: 'ANANDA COMUNIDAD · by Sara Garcini',
    hero: '把你的设计，变成一件可珍藏的人生之物。',
    lead: '以结构化精度计算、验证与诠释 Human Design，并以可长期保存的编辑设计呈现。',
    cta: '生成我的地图',
    sample: '查看 Regina 示例',
    calc: '计算图谱',
    calculating: '计算中…',
    name: '姓名',
    date: '出生日期',
    time: '准确时间',
    place: '出生地',
    zone: 'IANA 时区',
    focus: '你最想理解什么？',
    child: '儿童 / 亲子解读',
    generate: '生成深度解读',
    generating: '生成中…',
    pdf: '下载 PDF',
    zip: '下载 ZIP',
    save: '保存',
    buy: '购买',
    pending: '安全支付尚待配置',
    methodTitle: '编辑方法',
    methodBody:
      'ANANDA 将机械数据与解释层分开。类型、策略、权威、人生角色、定义、中心、通道与轮回交叉先被验证，再转化为深度、温和且非决定论的文字。',
    ep: 'Human Design 在此作为象征性、解释性的自我观察框架，而不是临床工具或经实证验证的科学。',
    products: '个人版本',
    lib: '我的档案',
    empty: '尚无保存的图谱。',
    provider: '计算引擎',
    connected: '已连接',
    waiting: '待连接',
    deep: '深度解读',
    import: '导入已验证 JSON',
    invalid: '请填写姓名、日期、时间、地点和时区。',
    api: '实时计算还需配置安全 API 密钥。Regina 示例和已验证 JSON 导入已可使用。',
    saved: '已保存。',
    readerr: '无法生成解读，请重试。',
    calcerr: '无法计算图谱，请检查数据或配置。',
    subtitle: 'Human Design · Personal Maps',
    disclaimer: '一张用来观察自己的地图，而不是把自己锁住的标签。',
  },
  ru: {
    create: 'Создать карту',
    method: 'Метод',
    editions: 'Издания',
    library: 'Библиотека',
    login: 'Войти',
    logout: 'Выйти',
    eyebrow: 'ANANDA COMUNIDAD · by Sara Garcini',
    hero: 'Ваш дизайн как объект на всю жизнь.',
    lead: 'Расчёт, проверка и глубокая интерпретация Human Design в премиальном редакционном формате.',
    cta: 'Создать мою карту',
    sample: 'Посмотреть пример Regina',
    calc: 'Рассчитать карту',
    calculating: 'Расчёт…',
    name: 'Полное имя',
    date: 'Дата рождения',
    time: 'Точное время',
    place: 'Место рождения',
    zone: 'Часовой пояс IANA',
    focus: 'Что вы хотите понять глубже?',
    child: 'Детское / родительское чтение',
    generate: 'Создать глубокое чтение',
    generating: 'Создаётся…',
    pdf: 'Скачать PDF',
    zip: 'Скачать ZIP',
    save: 'Сохранить',
    buy: 'Купить',
    pending: 'Безопасная оплата ожидает настройки',
    methodTitle: 'Редакционный метод',
    methodBody:
      'ANANDA разделяет механику и интерпретацию. Тип, Стратегия, Авторитет, Профиль, Определение, Центры, Каналы и Крест сначала проверяются, а затем переводятся в глубокий и недетерминистский текст.',
    ep: 'Human Design представлен здесь как символическая интерпретационная система самонаблюдения, а не клинический инструмент или эмпирически подтверждённая наука.',
    products: 'Персональные издания',
    lib: 'Моя библиотека',
    empty: 'Сохранённых карт пока нет.',
    provider: 'Модуль расчёта',
    connected: 'Подключён',
    waiting: 'Ожидает',
    deep: 'Глубокое чтение',
    import: 'Импорт проверенного JSON',
    invalid: 'Заполните имя, дату, время, место и часовой пояс.',
    api: 'Для расчёта в реальном времени нужен защищённый ключ провайдера. Пример Regina и импорт JSON уже работают.',
    saved: 'Сохранено.',
    readerr: 'Не удалось создать чтение.',
    calcerr: 'Не удалось рассчитать карту.',
    subtitle: 'Human Design · Personal Maps',
    disclaimer: 'Карта для наблюдения за собой, а не ярлык.',
  },
  ar: {
    create: 'إنشاء الخريطة',
    method: 'المنهج',
    editions: 'الإصدارات',
    library: 'المكتبة',
    login: 'دخول',
    logout: 'خروج',
    eyebrow: 'ANANDA COMUNIDAD · by Sara Garcini',
    hero: 'تصميمك، في صورة أثر شخصي للحياة.',
    lead: 'حساب Human Design والتحقق منه وتفسيره بعمق، ضمن إخراج تحريري راقٍ صُمم للاحتفاظ به.',
    cta: 'أنشئ خريطتي',
    sample: 'عرض مثال Regina',
    calc: 'احسب الخريطة',
    calculating: 'جارٍ الحساب…',
    name: 'الاسم الكامل',
    date: 'تاريخ الميلاد',
    time: 'الوقت الدقيق',
    place: 'مكان الميلاد',
    zone: 'المنطقة الزمنية IANA',
    focus: 'ما الذي تريد فهمه بعمق؟',
    child: 'قراءة للطفل / التربية',
    generate: 'أنشئ القراءة العميقة',
    generating: 'جارٍ الصياغة…',
    pdf: 'تنزيل PDF',
    zip: 'تنزيل ZIP',
    save: 'حفظ',
    buy: 'شراء',
    pending: 'الدفع الآمن ينتظر الإعداد',
    methodTitle: 'المنهج التحريري',
    methodBody:
      'يفصل ANANDA بين الميكانيكا والتفسير. يتم أولاً التحقق من النوع والاستراتيجية والسلطة والملف والتعريف والمراكز والقنوات والصليب، ثم تُترجم إلى قراءة إنسانية عميقة وغير حتمية.',
    ep: 'يُقدَّم Human Design هنا كإطار رمزي وتفسيري لمعرفة الذات، وليس كأداة سريرية أو علم مثبت تجريبياً.',
    products: 'إصدارات شخصية',
    lib: 'مكتبتي',
    empty: 'لا توجد خرائط محفوظة بعد.',
    provider: 'محرك الحساب',
    connected: 'متصل',
    waiting: 'قيد الإعداد',
    deep: 'قراءة عميقة',
    import: 'استيراد JSON موثّق',
    invalid: 'أكمل الاسم والتاريخ والوقت والمكان والمنطقة الزمنية.',
    api: 'الحساب الفوري يحتاج إلى مفتاح مزود آمن. مثال Regina واستيراد JSON الموثق يعملان الآن.',
    saved: 'تم الحفظ.',
    readerr: 'تعذر إنشاء القراءة.',
    calcerr: 'تعذر حساب الخريطة.',
    subtitle: 'Human Design · Personal Maps',
    disclaimer: 'خريطة للملاحظة، لا ملصق للحبس.',
  },
};

const sample: Chart = {
  name: 'Regina Aaliyah González Castillo',
  birthDate: '2023-08-08',
  birthTime: '17:43',
  birthPlace: 'Ciudad de México, México',
  timezone: 'America/Mexico_City',
  type: 'Generator',
  strategy: 'To Respond',
  authority: 'Sacral',
  profile: '4/6',
  definition: 'Split Definition',
  signature: 'Satisfaction',
  notSelf: 'Frustration',
  incarnationCross: 'Right Angle Cross of the Sphinx 3 · 7/13 | 2/1',
  definedCenters: ['Head', 'Ajna', 'Spleen', 'Sacral', 'Root'],
  openCenters: ['Throat', 'G', 'Heart', 'Solar Plexus'],
  channels: ['64-47', '27-50', '3-60'],
  gates: [1, 2, 3, 7, 13, 27, 47, 50, 60, 64],
  source: 'ANANDA validated sample',
};

const centerSpec = [
  ['Head', 200, 28, 'triangle'],
  ['Ajna', 200, 92, 'triangle'],
  ['Throat', 200, 158, 'rect'],
  ['G', 200, 238, 'diamond'],
  ['Heart', 280, 258, 'triangle'],
  ['Spleen', 105, 292, 'triangle'],
  ['Solar Plexus', 295, 330, 'triangle'],
  ['Sacral', 200, 345, 'rect'],
  ['Root', 200, 425, 'rect'],
] as const;
function BodyGraph({ chart }: { chart: Chart }) {
  const yes = (n: string) =>
    chart.definedCenters.some(x => x.toLowerCase().includes(n.toLowerCase()));
  return (
    <svg
      className="bodygraph"
      viewBox="0 0 400 480"
      role="img"
      aria-label="Human Design BodyGraph"
    >
      <g className="links" stroke="currentColor" strokeWidth="3" opacity=".28">
        <path d="M200 55V92M200 120V158M200 188V214M200 266V345M200 375V425M177 245L120 292M223 245L280 258M232 270L290 330M120 310L180 345M280 345L220 345M115 320L185 425M290 350L215 425" />
      </g>
      {centerSpec.map(([n, x, y, s]) => {
        const fill = yes(n) ? 'var(--copper)' : 'var(--paper)';
        const common = { fill, stroke: 'currentColor', strokeWidth: 2 };
        return (
          <g key={n}>
            {s === 'triangle' ? (
              <polygon
                {...common}
                points={
                  x -
                  26 +
                  ',' +
                  (y + 28) +
                  ' ' +
                  x +
                  ',' +
                  (y - 26) +
                  ' ' +
                  (x + 26) +
                  ',' +
                  (y + 28)
                }
              />
            ) : s === 'diamond' ? (
              <polygon
                {...common}
                points={
                  x +
                  ',' +
                  (y - 35) +
                  ' ' +
                  (x + 35) +
                  ',' +
                  y +
                  ' ' +
                  x +
                  ',' +
                  (y + 35) +
                  ' ' +
                  (x - 35) +
                  ',' +
                  y
                }
              />
            ) : (
              <rect
                {...common}
                x={x - 28}
                y={y - 22}
                width="56"
                height="44"
                rx="5"
              />
            )}
            <text
              x={x}
              y={y + 4}
              textAnchor="middle"
              fontSize="9"
              fill="var(--ink)"
            >
              {n}
            </text>
          </g>
        );
      })}
      <text x="200" y="468" textAnchor="middle" className="svg-note">
        {chart.channels.join(' · ')}
      </text>
    </svg>
  );
}

function App() {
  const [locale, setLocale] = useState<Locale>(
    (localStorage.getItem('ananda-locale') as Locale) || 'es'
  );
  const [dark, setDark] = useState(
    localStorage.getItem('ananda-theme') === 'dark'
  );
  const [user, setUser] = useState<any>(null),
    [provider, setProvider] = useState(false),
    [payments, setPayments] = useState<Record<string, string>>({});
  const [chart, setChart] = useState<Chart | null>(null),
    [reading, setReading] = useState<Reading | null>(null),
    [busy, setBusy] = useState(false),
    [rBusy, setRBusy] = useState(false),
    [notice, setNotice] = useState('');
  const [library, setLibrary] = useState<any[]>([]);
  const [form, setForm] = useState({
    name: '',
    birthDate: '',
    birthTime: '',
    birthPlace: '',
    timezone: 'America/Mexico_City',
    focus: '',
    edition: 'core' as Edition,
    child: false,
  });
  const reportRef = useRef<HTMLDivElement>(null);
  const t = (k: string) => C[locale][k] || k;
  const dir = locale === 'ar' ? 'rtl' : 'ltr';
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    localStorage.setItem('ananda-theme', dark ? 'dark' : 'light');
  }, [dark]);
  useEffect(() => {
    localStorage.setItem('ananda-locale', locale);
    document.documentElement.lang = locale;
    document.documentElement.dir = dir;
  }, [locale, dir]);
  useEffect(() => {
    auth
      .getUser()
      .then(u => {
        setUser(u);
        if (u) loadLibrary();
      })
      .catch(() => {});
    api
      .get('/api/status')
      .then(r => setProvider(!!r.data.chartProvider))
      .catch(() => {});
    api
      .get('/api/payment-links')
      .then(r => setPayments(r.data || {}))
      .catch(() => {});
  }, []);
  const loadLibrary = async () => {
    try {
      const r = await api.get('/api/projects');
      setLibrary(r.data.items || []);
    } catch {}
  };
  const signin = async () => {
    try {
      const r = await auth.signIn();
      setUser(r.user);
      setTimeout(loadLibrary, 200);
    } catch {}
  };
  const signout = async () => {
    await auth.signOut();
    setUser(null);
    setLibrary([]);
  };
  const calculate = async (e: any) => {
    e.preventDefault();
    setNotice('');
    if (
      !form.name ||
      !form.birthDate ||
      !form.birthTime ||
      !form.birthPlace ||
      !form.timezone
    ) {
      setNotice(t('invalid'));
      return;
    }
    if (!provider) {
      setNotice(t('api'));
      return;
    }
    setBusy(true);
    try {
      const r = await api.post('/api/chart', form);
      setChart(r.data.chart);
      setReading(null);
      setTimeout(
        () =>
          document
            .getElementById('result')
            ?.scrollIntoView({ behavior: 'smooth' }),
        100
      );
    } catch {
      setNotice(t('calcerr'));
    } finally {
      setBusy(false);
    }
  };
  const loadSample = () => {
    setChart(sample);
    setForm({
      ...form,
      name: sample.name,
      birthDate: sample.birthDate,
      birthTime: sample.birthTime,
      birthPlace: sample.birthPlace,
      timezone: sample.timezone,
      edition: 'child',
      child: true,
    });
    setReading(null);
    setTimeout(
      () =>
        document
          .getElementById('result')
          ?.scrollIntoView({ behavior: 'smooth' }),
      100
    );
  };
  const gen = async () => {
    if (!chart) return;
    setRBusy(true);
    setNotice('');
    try {
      const r = await api.post('/api/reading', {
        chart,
        locale,
        focus: form.focus,
        child: form.child,
        edition: form.edition,
      });
      setReading(r.data.reading);
    } catch {
      setNotice(t('readerr'));
    } finally {
      setRBusy(false);
    }
  };
  const save = async () => {
    if (!chart) return;
    if (!user) {
      await signin();
      return;
    }
    try {
      await api.post('/api/projects', {
        chart,
        reading,
        edition: form.edition,
        locale,
      });
      setNotice(t('saved'));
      loadLibrary();
    } catch {}
  };
  const pdf = async () => {
    if (!reportRef.current || !chart) return;
    const canvas = await html2canvas(reportRef.current, {
      scale: 1.6,
      backgroundColor: dark ? '#121110' : '#f4f0e8',
    });
    const p = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    const w = 190,
      h = (canvas.height * w) / canvas.width;
    const img = canvas.toDataURL('image/jpeg', 0.9);
    let y = 10,
      remain = h;
    p.addImage(img, 'JPEG', 10, y, w, h);
    remain -= 277;
    while (remain > 0) {
      p.addPage();
      y = 10 - (h - remain);
      p.addImage(img, 'JPEG', 10, y, w, h);
      remain -= 277;
    }
    p.save('ANANDA-DESIGN-' + chart.name.replace(/\s+/g, '-') + '.pdf');
  };
  const zip = async () => {
    if (!chart) return;
    const z = new JSZip();
    z.file('chart.json', JSON.stringify(chart, null, 2));
    if (reading) z.file('reading.json', JSON.stringify(reading, null, 2));
    z.file(
      'README.txt',
      'ANANDA DESIGN\\nHuman Design · Personal Maps\\nANANDA COMUNIDAD · by Sara Garcini\\n\\nSymbolic and interpretive self-knowledge framework.'
    );
    const svg = document.querySelector('.bodygraph')?.outerHTML || '';
    z.file('bodygraph.svg', svg);
    const b = await z.generateAsync({ type: 'blob' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(b);
    a.download = 'ANANDA-DESIGN-' + chart.name.replace(/\s+/g, '-') + '.zip';
    a.click();
    URL.revokeObjectURL(a.href);
  };
  const checkout = (ed: Edition) => {
    const u = payments[ed];
    if (u) window.open(u, '_blank', 'noopener,noreferrer');
    else setNotice(t('pending'));
  };
  const cards: [Edition, string, any, string][] = [
    ['seed', 'ANANDA SEED', Leaf, '$690 MXN'],
    ['core', 'ANANDA CORE', Compass, '$2,900 MXN'],
    ['signature', 'ANANDA SIGNATURE', BookOpen, '$5,900 MXN'],
    ['child', 'ANANDA CHILD', Baby, '$3,400 MXN'],
    ['duo', 'ANANDA DUO', Users, '$6,900 MXN'],
  ];
  const stats = useMemo(
    () =>
      chart
        ? [
            ['TYPE', chart.type],
            ['STRATEGY', chart.strategy],
            ['AUTHORITY', chart.authority],
            ['PROFILE', chart.profile],
            ['DEFINITION', chart.definition],
            ['SIGNATURE', chart.signature],
          ]
        : [],
    [chart]
  );
  return (
    <div className="shell" dir={dir}>
      <header>
        <a href="#top" className="brand">
          <b>ANANDA</b>
          <span>DESIGN</span>
        </a>
        <nav>
          <a href="#create">{t('create')}</a>
          <a href="#method">{t('method')}</a>
          <a href="#editions">{t('editions')}</a>
          <a href="#library">{t('library')}</a>
        </nav>
        <div className="tools">
          <select
            value={locale}
            onChange={e => setLocale(e.target.value as Locale)}
          >
            <option value="es">ES</option>
            <option value="en">EN</option>
            <option value="de">DE</option>
            <option value="zh">中文</option>
            <option value="ru">RU</option>
            <option value="ar">العربية</option>
          </select>
          <button className="icon" onClick={() => setDark(!dark)}>
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button className="login" onClick={user ? signout : signin}>
            {user ? <LogOut size={16} /> : <LogIn size={16} />}{' '}
            {user ? t('logout') : t('login')}
          </button>
        </div>
      </header>
      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">{t('eyebrow')}</p>
            <h1>{t('hero')}</h1>
            <p className="lead">{t('lead')}</p>
            <div className="buttons">
              <a className="primary" href="#create">
                {t('cta')}
              </a>
              <button className="ghost" onClick={loadSample}>
                {t('sample')}
              </button>
            </div>
            <div className="trust">
              <span>
                <Check size={14} /> CALCULATION
              </span>
              <span>
                <Check size={14} /> CURATION
              </span>
              <span>
                <Check size={14} /> PDF + ZIP
              </span>
              <span>
                <Check size={14} /> 6 LANGUAGES
              </span>
            </div>
          </div>
          <div className="hero-card">
            <div className="card-cap">PERSONAL MAP · 001</div>
            <BodyGraph chart={sample} />
            <strong>GENERATOR</strong>
            <span>SACRAL · 4/6</span>
          </div>
        </section>
        <section id="create" className="section create">
          <div className="section-title">
            <p className="eyebrow">01 · GENERATE</p>
            <h2>ANANDA DESIGN</h2>
            <p>{t('lead')}</p>
          </div>
          <div className="create-grid">
            <form onSubmit={calculate} className="panel form">
              <div className="provider">
                <span>{t('provider')}</span>
                <b className={provider ? 'ok' : ''}>
                  <ShieldCheck size={14} />
                  {provider ? t('connected') : t('waiting')}
                </b>
              </div>
              <label>
                {t('name')}
                <input
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                />
              </label>
              <div className="two">
                <label>
                  {t('date')}
                  <input
                    type="date"
                    value={form.birthDate}
                    onChange={e =>
                      setForm({ ...form, birthDate: e.target.value })
                    }
                  />
                </label>
                <label>
                  {t('time')}
                  <input
                    type="time"
                    value={form.birthTime}
                    onChange={e =>
                      setForm({ ...form, birthTime: e.target.value })
                    }
                  />
                </label>
              </div>
              <label>
                {t('place')}
                <input
                  value={form.birthPlace}
                  onChange={e =>
                    setForm({ ...form, birthPlace: e.target.value })
                  }
                  placeholder="Ciudad de México, México"
                />
              </label>
              <label>
                {t('zone')}
                <input
                  value={form.timezone}
                  onChange={e => setForm({ ...form, timezone: e.target.value })}
                  placeholder="America/Mexico_City"
                />
              </label>
              <label>
                {t('focus')}
                <textarea
                  rows={3}
                  value={form.focus}
                  onChange={e => setForm({ ...form, focus: e.target.value })}
                />
              </label>
              <label className="check">
                <input
                  type="checkbox"
                  checked={form.child}
                  onChange={e => setForm({ ...form, child: e.target.checked })}
                />
                {t('child')}
              </label>
              <button className="primary wide" disabled={busy}>
                {busy ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <Sparkles size={17} />
                )}{' '}
                {busy ? t('calculating') : t('calc')}
              </button>
              <button type="button" className="text" onClick={loadSample}>
                {t('sample')}
              </button>
            </form>
            <aside className="panel manifesto">
              <div className="monogram">A</div>
              <h3>
                CALCULATED WITH PRECISION.
                <br />
                INTERPRETED WITH CARE.
                <br />
                DESIGNED FOR ONE PERSON.
              </h3>
              <p>{t('ep')}</p>
              <blockquote>UN MAPA PARA VOLVER A TI.</blockquote>
            </aside>
          </div>
          {notice && <div className="notice">{notice}</div>}
        </section>
        {chart && (
          <section id="result" className="section result" ref={reportRef}>
            <div className="result-head">
              <div>
                <p className="eyebrow">ANANDA DESIGN · PERSONAL MAP</p>
                <h2>{chart.name}</h2>
                <p>
                  {chart.birthDate} · {chart.birthTime} · {chart.birthPlace}
                </p>
              </div>
              <div className="result-tools">
                <button onClick={pdf}>
                  <Download size={15} />
                  {t('pdf')}
                </button>
                <button onClick={zip}>
                  <FileArchive size={15} />
                  {t('zip')}
                </button>
                <button onClick={save}>
                  <Save size={15} />
                  {t('save')}
                </button>
              </div>
            </div>
            <div className="chart-grid">
              <div className="graph">
                <BodyGraph chart={chart} />
              </div>
              <div className="stats">
                {stats.map(([k, v]) => (
                  <div key={k}>
                    <span>{k}</span>
                    <b>{v || '—'}</b>
                  </div>
                ))}
                <div className="span">
                  <span>INCARNATION CROSS</span>
                  <b>{chart.incarnationCross || '—'}</b>
                </div>
              </div>
            </div>
            <div className="micro">
              <article>
                <span>DEFINED</span>
                <p>{chart.definedCenters.join(' · ')}</p>
              </article>
              <article>
                <span>OPEN</span>
                <p>{chart.openCenters.join(' · ')}</p>
              </article>
              <article>
                <span>CHANNELS</span>
                <p>{chart.channels.join(' · ')}</p>
              </article>
            </div>
            <div className="reading">
              <div className="reading-head">
                <div>
                  <p className="eyebrow">02 · INTERPRET</p>
                  <h2>{t('deep')}</h2>
                </div>
                <button className="primary" onClick={gen} disabled={rBusy}>
                  {rBusy ? (
                    <LoaderCircle className="spin" size={17} />
                  ) : (
                    <Sparkles size={17} />
                  )}{' '}
                  {rBusy ? t('generating') : t('generate')}
                </button>
              </div>
              {reading ? (
                <div className="reading-copy">
                  <h3>{reading.title}</h3>
                  <p className="subtitle">{reading.subtitle}</p>
                  <p className="opening">{reading.opening}</p>
                  {reading.sections.map((s, i) => (
                    <article key={i}>
                      <span>{String(i + 1).padStart(2, '0')}</span>
                      <div>
                        <h4>{s.heading}</h4>
                        <p>{s.body}</p>
                        {s.practice && (
                          <p className="note">ANANDA NOTE · {s.practice}</p>
                        )}
                      </div>
                    </article>
                  ))}
                  <p className="closing">{reading.closing}</p>
                </div>
              ) : (
                <p className="empty">
                  Human Design becomes useful here: structure first,
                  interpretation second, practice third.
                </p>
              )}
            </div>
          </section>
        )}
        <section id="method" className="section method">
          <div>
            <p className="eyebrow">03 · METHOD</p>
            <h2>{t('methodTitle')}</h2>
            <p className="big">{t('methodBody')}</p>
            <p className="ep">{t('ep')}</p>
          </div>
          <div className="flow">
            <div>
              MECHANICS<small>type · strategy · authority</small>
            </div>
            <i />
            <div>
              CURATION<small>canon · validation · context</small>
            </div>
            <i />
            <div>
              INTERPRETATION<small>depth · poetry · practice</small>
            </div>
            <i />
            <div>
              EDITION<small>book · pdf · archive</small>
            </div>
          </div>
        </section>
        <section id="editions" className="section">
          <div className="section-title">
            <p className="eyebrow">04 · PRODUCT</p>
            <h2>{t('products')}</h2>
          </div>
          <div className="products">
            {cards.map(([id, n, Icon, price]) => (
              <article className={id === 'core' ? 'featured' : ''} key={id}>
                <Icon size={21} />
                <h3>{n}</h3>
                <p>
                  {id === 'seed'
                    ? 'Type · Strategy · Authority'
                    : id === 'core'
                      ? 'Complete personal chart + deep reading'
                      : id === 'signature'
                        ? 'Premium heirloom edition + extended interpretation'
                        : id === 'child'
                          ? 'Child chart + parenting observation guide'
                          : 'Two charts + relational dynamics'}
                </p>
                <strong>{price}</strong>
                <button onClick={() => checkout(id)}>{t('buy')}</button>
              </article>
            ))}
          </div>
        </section>
        <section id="library" className="section archive">
          <div className="section-title">
            <p className="eyebrow">05 · ARCHIVE</p>
            <h2>{t('lib')}</h2>
          </div>
          {user ? (
            <div className="library">
              {library.length ? (
                library.map((p: any) => (
                  <article key={p.id}>
                    <UserRound size={18} />
                    <b>{p.name}</b>
                    <span>
                      {p.type} · {p.profile}
                    </span>
                  </article>
                ))
              ) : (
                <p className="empty">{t('empty')}</p>
              )}
            </div>
          ) : (
            <div className="signin">
              <UserRound />
              <p>Google · X · Email</p>
              <button className="primary" onClick={signin}>
                {t('login')}
              </button>
            </div>
          )}
        </section>
      </main>
      <footer>
        <div className="brand">
          <b>ANANDA</b>
          <span>DESIGN</span>
        </div>
        <p>{t('disclaimer')}</p>
        <span>© 2026 ANANDA COMUNIDAD · Sara Garcini</span>
      </footer>
    </div>
  );
}
export default App;
