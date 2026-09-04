import { useRef, useState, type ReactNode } from "react";
import styles from "./Carousel.module.css";

type Props = {
  children: ReactNode[];
  ariaLabel: string;
  /** Quantos slides ficam visíveis por vez no desktop (mobile é sempre 1, cheio). Default: 3. */
  slidesPerView?: number;
};

/**
 * Carrossel genérico: scroll-snap nativo (funciona por swipe no celular,
 * regra mobile-first da skill dev-frontend) + setas para desktop. Sem
 * lib de terceiro — scroll-snap nativo já resolve o caso de uso.
 *
 * slidesPerView controla a LARGURA do slide (via --carousel-slides
 * consumida no CSS) — o índice ativo é sempre calculado pela largura
 * real de UM slide, nunca por clientWidth do track inteiro, senão os
 * dots/setas dessincronizam do que está de fato visível.
 */
export function Carousel({ children, ariaLabel, slidesPerView = 3 }: Props) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  function scrollToIndex(index: number) {
    const track = trackRef.current;
    if (!track) return;
    const clamped = Math.max(0, Math.min(children.length - 1, index));
    const child = track.children[clamped] as HTMLElement | undefined;
    child?.scrollIntoView({ behavior: "smooth", inline: "start", block: "nearest" });
  }

  function handleScroll() {
    const track = trackRef.current;
    if (!track) return;
    const firstSlide = track.children[0] as HTMLElement | undefined;
    const slideWidth = firstSlide?.getBoundingClientRect().width || track.clientWidth;
    const gap = 16;
    const index = Math.round(track.scrollLeft / (slideWidth + gap));
    setActiveIndex(Math.max(0, Math.min(children.length - 1, index)));
  }

  return (
    <div
      className={styles.carousel}
      aria-label={ariaLabel}
      role="region"
      style={{ "--carousel-slides": slidesPerView } as React.CSSProperties}
    >
      <div className={styles.trackWrapper}>
        <button
          type="button"
          className={styles.navBtn}
          onClick={() => scrollToIndex(activeIndex - 1)}
          disabled={activeIndex <= 0}
          aria-label="Anterior"
        >
          ←
        </button>

        <div className={styles.track} ref={trackRef} onScroll={handleScroll}>
          {children.map((child, i) => (
            <div className={styles.slide} key={i}>
              {child}
            </div>
          ))}
        </div>

        <button
          type="button"
          className={styles.navBtn}
          onClick={() => scrollToIndex(activeIndex + 1)}
          disabled={activeIndex >= children.length - 1}
          aria-label="Próximo"
        >
          →
        </button>
      </div>

      {children.length > 1 && (
        <div className={styles.dots}>
          {children.map((_, i) => (
            <button
              key={i}
              type="button"
              className={i === activeIndex ? `${styles.dot} ${styles.dotActive}` : styles.dot}
              onClick={() => scrollToIndex(i)}
              aria-label={`Ir para item ${i + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
