import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';
import AppLogo from '../components/AppLogo.jsx';

const fadeUp = {
  hidden: { opacity: 0, y: 44 },
  visible: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: i * 0.12 },
  }),
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.10 } },
};

function SectionTitle({ children, subtitle }) {
  return (
    <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-80px' }} variants={stagger} className="max-w-3xl mx-auto flex flex-col items-center text-center mb-12 md:mb-16">
      <motion.h2 variants={fadeUp} className="mb-3 text-4xl md:text-5xl font-bold text-slate-900 tracking-tight">{children}</motion.h2>
      {subtitle && (<motion.p variants={fadeUp} className="text-slate-600 text-lg leading-relaxed max-w-2xl mx-auto text-center">{subtitle}</motion.p>)}
      <motion.div variants={fadeUp} className="mt-5 mx-auto w-20 h-1 bg-rose-600 rounded-full" />
    </motion.div>
  );
}

const slides = [
  { title: 'Bienvenue sur SmartPointage', subtitle: "Le système officiel d'émargement et de gestion des présences de Ménara Préfa.", bg: 'https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=1600&q=80', alt: 'Collaborateur utilisant un terminal professionnel pour son pointage SmartPointage' },
  { title: 'Votre espace collaborateur', subtitle: 'Pointez, consultez vos informations et suivez vos demandes RH depuis un espace unique.', bg: 'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=1600&q=80', alt: 'Poste de travail moderne pour accéder à SmartPointage' },
  { title: 'Une présence suivie au quotidien', subtitle: 'Les managers disposent des informations nécessaires pour accompagner leurs équipes.', bg: 'https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=1600&q=80', alt: 'Manager échangeant avec une équipe autour du suivi des présences' },
];

const poles = [
  { title: 'Pointage par reconnaissance faciale', desc: 'Un passage simple et sécurisé au pointeur pour enregistrer votre présence.', icon: (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="w-8 h-8"><circle cx="12" cy="8" r="4" /><path d="M5 20c1-4 4-6 7-6s6 2 7 6" strokeLinecap="round" /><rect x="3" y="3" width="18" height="18" rx="3" /></svg>) },
  { title: 'Consultation des plannings', desc: 'Retrouvez vos horaires, vos pointages et les informations utiles à votre journée.', icon: (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="w-8 h-8"><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M7 2v4M17 2v4M3 9h18M7 13h3M7 17h6" strokeLinecap="round" /></svg>) },
  { title: 'Suivi des retards', desc: 'Une visibilité claire sur les horaires et le suivi quotidien des présences.', icon: (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="w-8 h-8"><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3 2" strokeLinecap="round" /></svg>) },
  { title: 'Validation des demandes RH', desc: 'Les managers traitent les demandes de congé et de télétravail au même endroit.', icon: (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="w-8 h-8"><path d="M5 12.5 9.5 17 19 7.5" strokeLinecap="round" strokeLinejoin="round" /><rect x="3" y="3" width="18" height="18" rx="3" /></svg>) },
];

export default function Landing() {
  const navigate = useNavigate();
  const [slideIdx, setSlideIdx] = useState(0);
  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.15], [1, 0.95]);

  useEffect(() => {
    const t = setInterval(() => setSlideIdx((i) => (i + 1) % slides.length), 5000);
    return () => clearInterval(t);
  }, []);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="font-sans text-slate-800 bg-white overflow-x-hidden">
      <motion.header initial={{ y: -60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="fixed top-0 left-0 right-0 z-50 px-6 md:px-10 py-3 flex items-center justify-between bg-white/75 backdrop-blur-xl border-b border-slate-200/60 shadow-xs">
        <div className="flex items-center gap-2.5">
          <AppLogo size={32} />
          <div>
            <div className="font-bold text-lg tracking-tight text-slate-900 leading-tight">Ménara Préfa</div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-rose-600">SmartPointage</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="hidden sm:inline-flex text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors px-3 py-2">Se connecter</Link>
          <Link to="/login" className="inline-flex items-center gap-1.5 text-sm font-semibold text-white bg-rose-600 hover:bg-rose-700 px-5 py-2.5 rounded-lg shadow-lg shadow-rose-600/25 hover:shadow-rose-600/35 transition-all duration-300 hover:scale-105 active:scale-95">
            Accéder à l'espace collaborateur
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14m-7-7 7 7-7 7"/></svg>
          </Link>
        </div>
      </motion.header>

      <motion.section id="hero" style={{ opacity: heroOpacity, scale: heroScale }} className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div key={slideIdx} initial={{ opacity: 0, scale: 1.02 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.02 }}
            transition={{ duration: 1.8, ease: 'easeInOut' }} className="absolute inset-0">
            <img src={slides[slideIdx].bg} alt={slides[slideIdx].alt} className="w-full h-full object-cover object-center" />
          </motion.div>
        </AnimatePresence>
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900/75 via-slate-900/60 to-slate-900/80" />

        <div className="relative z-10 max-w-3xl mx-auto flex flex-col items-center text-center px-6">
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }}
            className="text-rose-400 font-semibold text-sm md:text-base tracking-widest uppercase mb-4">
            Portail collaborateur officiel
          </motion.p>
          <motion.h1 key={slides[slideIdx].title} initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="mb-4 text-4xl sm:text-5xl md:text-7xl font-bold text-white leading-[1.12] tracking-tight whitespace-pre-line">
            {slides[slideIdx].title}
          </motion.h1>
          <motion.p key={slides[slideIdx].subtitle} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-slate-300 text-lg md:text-xl leading-relaxed max-w-2xl mx-auto">
            {slides[slideIdx].subtitle}
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.35 }}
            className="mt-6 flex flex-wrap justify-center items-center gap-4">
            <button onClick={() => navigate('/login')}
              className="inline-flex items-center gap-2 text-base font-semibold text-white bg-rose-600 hover:bg-rose-700 px-8 py-3.5 rounded-xl shadow-2xl shadow-rose-600/30 hover:shadow-rose-600/40 transition-all duration-300 hover:scale-105 active:scale-95">
              Accéder à mon espace
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14m-7-7 7 7-7 7"/></svg>
            </button>
            <button onClick={() => scrollTo('poles')}
              className="inline-flex items-center gap-2 text-base font-medium text-white/80 hover:text-white px-8 py-3.5 rounded-xl border border-white/30 hover:border-white/50 transition-all duration-300 hover:scale-105 active:scale-95">
              Voir les outils disponibles
            </button>
          </motion.div>

          <div className="absolute -bottom-20 left-1/2 -translate-x-1/2 flex gap-2.5">
            {slides.map((_, i) => (
              <button key={i} onClick={() => setSlideIdx(i)}
                className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${i === slideIdx ? 'bg-rose-500 w-8' : 'bg-white/40 hover:bg-white/60'}`} />
            ))}
          </div>
          </div>
      </motion.section>
      

      <section id="poles" className="px-6 py-12 md:py-20 bg-slate-50/60">
        <SectionTitle subtitle="Des fonctionnalités conçues pour simplifier le quotidien des collaborateurs et le suivi des équipes.">
          Les outils mis à votre disposition
        </SectionTitle>
        <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }} variants={stagger}
          className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {poles.map((pole, i) => (
            <motion.div key={pole.title} variants={fadeUp} custom={i}
              className="group bg-white rounded-2xl p-7 border border-slate-100 shadow-md shadow-slate-100/50 hover:shadow-xl hover:shadow-slate-200/60 hover:-translate-y-1.5 transition-all duration-300 text-center">
              <div className="mx-auto w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center mb-5 group-hover:bg-rose-600 group-hover:text-white transition-colors duration-300">{pole.icon}</div>
              <h3 className="mb-3 text-lg font-bold text-slate-900">{pole.title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{pole.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section className="px-6 py-12 md:py-20 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-rose-500 blur-[120px]" />
          <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-rose-500 blur-[120px]" />
        </div>
        <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="relative z-10 max-w-3xl mx-auto flex flex-col items-center text-center">
          <motion.h2 variants={fadeUp} className="mb-3 text-3xl md:text-5xl font-bold text-white tracking-tight">Votre espace de pointage officiel</motion.h2>
          <motion.p variants={fadeUp} className="text-slate-400 text-lg leading-relaxed max-w-2xl mx-auto">Connectez-vous avec vos identifiants Ménara Préfa pour accéder à vos services.</motion.p>
          <motion.div variants={fadeUp} className="mt-6 flex justify-center items-center">
            <button onClick={() => navigate('/login')}
              className="inline-flex items-center gap-2 text-base font-semibold text-white bg-rose-600 hover:bg-rose-700 px-10 py-4 rounded-xl shadow-2xl shadow-rose-600/30 hover:shadow-rose-600/40 transition-all duration-300 hover:scale-105 active:scale-95">
              Accéder à l'espace collaborateur
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14m-7-7 7 7-7 7"/></svg>
            </button>
          </motion.div>
        </motion.div>
      </section>

      <footer id="contact" className="bg-slate-950 text-slate-400 px-6 py-16 border-t border-slate-800">
        <div className="max-w-6xl mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
          <div>
            <div className="flex items-center gap-2.5 mb-5">
              <AppLogo size={28} />
              <div>
                <div className="font-bold text-lg tracking-tight text-white leading-tight">Ménara Préfa</div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-rose-400">SmartPointage</div>
              </div>
            </div>
            <p className="text-sm leading-relaxed text-slate-500">Portail interne de pointage et de gestion des présences du Groupe Ménara.</p>
          </div>
          <div>
            <h4 className="font-semibold text-white text-sm uppercase tracking-wider mb-4">Accès</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/login" className="hover:text-white transition-colors">Espace collaborateur</Link></li>
              <li><button onClick={() => scrollTo('poles')} className="hover:text-white transition-colors">Outils disponibles</button></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-white text-sm uppercase tracking-wider mb-4">Accompagnement interne</h4>
            <ul className="space-y-2.5 text-sm">
              <li>Support informatique interne</li>
              <li>Direction des Ressources Humaines</li>
              <li>Assistance pour les accès et le pointage</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-white text-sm uppercase tracking-wider mb-4">Confidentialité</h4>
            <ul className="space-y-2.5 text-sm">
              <li><span className="hover:text-white transition-colors cursor-pointer">Mentions de confidentialité</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Données de présence protégées</span></li>
            </ul>
          </div>
        </div>
        <div className="mt-14 pt-8 border-t border-slate-800 text-center text-xs text-slate-600">
          &copy; {new Date().getFullYear()} Groupe Ménara · SmartPointage. Portail interne réservé aux collaborateurs.
        </div>
      </footer>
    </div>
  );
}
