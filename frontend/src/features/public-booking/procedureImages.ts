/**
 * Biblioteca de imagens de alta qualidade curadas para clínicas de estética médica.
 * Vincula inteligentemente o procedimento à sua foto representativa com base em palavras-chave.
 */

const PROCEDURE_PHOTO_MAP: Record<string, string> = {
  limpeza: "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=600&q=80",
  pele: "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=600&q=80",
  harmonizacao: "https://images.unsplash.com/photo-1512290900672-1f55b91b9758?auto=format&fit=crop&w=600&q=80",
  preenchimento: "https://images.unsplash.com/photo-1512290900672-1f55b91b9758?auto=format&fit=crop&w=600&q=80",
  labial: "https://images.unsplash.com/photo-1588510906202-b0682ba7bbcf?auto=format&fit=crop&w=600&q=80",
  peeling: "https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?auto=format&fit=crop&w=600&q=80",
  botox: "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80",
  toxina: "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80",
  laser: "https://images.unsplash.com/photo-1560750588-73207b1ef5b8?auto=format&fit=crop&w=600&q=80",
  depilacao: "https://images.unsplash.com/photo-1560750588-73207b1ef5b8?auto=format&fit=crop&w=600&q=80",
  drenagem: "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=600&q=80",
  massagem: "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=600&q=80",
  corporal: "https://images.unsplash.com/photo-1519823551278-64ac92734fb1?auto=format&fit=crop&w=600&q=80",
  microagulhamento: "https://images.unsplash.com/photo-1512290903422-92143003058b?auto=format&fit=crop&w=600&q=80",
  fios: "https://images.unsplash.com/photo-1512290900672-1f55b91b9758?auto=format&fit=crop&w=600&q=80",
  facial: "https://images.unsplash.com/photo-1629732047847-50219e9c5aef?auto=format&fit=crop&w=600&q=80",
};

const DEFAULT_PROCEDURE_PHOTO =
  "https://images.unsplash.com/photo-1629732047847-50219e9c5aef?auto=format&fit=crop&w=600&q=80";

export function getProcedurePhoto(name: string): string {
  const normalized = name
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

  for (const [key, url] of Object.entries(PROCEDURE_PHOTO_MAP)) {
    if (normalized.includes(key)) {
      return url;
    }
  }

  return DEFAULT_PROCEDURE_PHOTO;
}
