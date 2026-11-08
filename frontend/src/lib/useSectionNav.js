/**
 * useSectionNav — Logika tombol PLTU/PLTN di header (dipakai Dashboard & Data View).
 *
 * - registerSection(value) → ref callback untuk elemen section
 * - scrollToSection(value) → klik tombol header: scroll ke section
 * - activeSection          → tombol yang aktif, ikut berubah saat user scroll manual
 *
 * watch: nilai yang kalau berubah berarti section di-render ulang
 * (mis. data selesai dimuat), supaya observer dipasang ulang.
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export default function useSectionNav(sections, watch) {
  const [activeSection, setActiveSection] = useState(sections[0]?.value);
  const sectionRefs = useRef({});

  useEffect(() => {
    const elements = Object.values(sectionRefs.current).filter(Boolean);
    if (!elements.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveSection(entry.target.id);
        });
      },
      { rootMargin: "-100px 0px -50% 0px", threshold: 0 }
    );

    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [watch]);

  const scrollToSection = useCallback((value) => {
    setActiveSection(value);
    sectionRefs.current[value]?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const registerSection = useCallback(
    (value) => (element) => {
      sectionRefs.current[value] = element;
    },
    []
  );

  return { activeSection, scrollToSection, registerSection };
}
