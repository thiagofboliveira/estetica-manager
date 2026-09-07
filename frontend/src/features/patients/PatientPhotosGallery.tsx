import { useState, useMemo, useRef } from "react";
import styles from "./PatientPhotosGallery.module.css";
import {
  useCreatePatientPhoto,
  useDeletePatientPhoto,
  usePatientPhotos,
} from "./usePatientPhotos";
import { useProcedures } from "@/features/procedures/hooks";
import { compressImage } from "./imageUtils";
import type { PatientPhoto, PhotoType } from "./photosApi";

interface PatientPhotosGalleryProps {
  patientId: string;
  patientName: string;
}

export function PatientPhotosGallery({
  patientId,
  patientName,
}: PatientPhotosGalleryProps) {
  const [viewMode, setViewMode] = useState<"grid" | "compare">("grid");
  const [filterType, setFilterType] = useState<PhotoType | "ALL">("ALL");
  const [filterProcedureId, setFilterProcedureId] = useState<string>("ALL");

  // Modal de nova foto
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [photoType, setPhotoType] = useState<PhotoType>("BEFORE");
  const [procedureId, setProcedureId] = useState<string>("");
  const [caption, setCaption] = useState<string>("");
  const [capturedAt, setCapturedAt] = useState<string>(
    new Date().toISOString().slice(0, 10)
  );
  const [authorizedSocialMedia, setAuthorizedSocialMedia] = useState(false);
  const [isCompressing, setIsCompressing] = useState(false);

  // Lightbox
  const [lightboxPhoto, setLightboxPhoto] = useState<PatientPhoto | null>(null);

  // Seletores para o modo comparador
  const [compareBeforeId, setCompareBeforeId] = useState<string>("");
  const [compareAfterId, setCompareAfterId] = useState<string>("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Queries e Mutações
  const photosQuery = usePatientPhotos(patientId, {
    photo_type: filterType !== "ALL" ? filterType : undefined,
    procedure_id: filterProcedureId !== "ALL" ? filterProcedureId : undefined,
  });
  const proceduresQuery = useProcedures();
  const createPhotoMutation = useCreatePatientPhoto(patientId);
  const deletePhotoMutation = useDeletePatientPhoto(patientId);

  const photos = useMemo(() => photosQuery.data || [], [photosQuery.data]);
  const procedures = useMemo(() => proceduresQuery.data || [], [proceduresQuery.data]);

  // Fotos para o comparador
  const beforePhotos = useMemo(
    () => photos.filter((p) => p.photo_type === "BEFORE"),
    [photos]
  );
  const afterPhotos = useMemo(
    () => photos.filter((p) => p.photo_type === "AFTER"),
    [photos]
  );

  // Auto-seleciona primeiro Antes e primeiro Depois no modo comparador se não definidos
  const selectedBefore = useMemo(() => {
    if (compareBeforeId) {
      return photos.find((p) => p.id === compareBeforeId) || null;
    }
    return beforePhotos[0] || null;
  }, [photos, compareBeforeId, beforePhotos]);

  const selectedAfter = useMemo(() => {
    if (compareAfterId) {
      return photos.find((p) => p.id === compareAfterId) || null;
    }
    return afterPhotos[0] || null;
  }, [photos, compareAfterId, afterPhotos]);

  const diffDays = useMemo(() => {
    if (!selectedBefore || !selectedAfter) return null;
    const d1 = new Date(selectedBefore.captured_at).getTime();
    const d2 = new Date(selectedAfter.captured_at).getTime();
    const days = Math.round(Math.abs(d2 - d1) / (1000 * 60 * 60 * 24));
    return days;
  }, [selectedBefore, selectedAfter]);

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsCompressing(true);
    try {
      const compressedDataUrl = await compressImage(file, 1280, 0.82);
      setPreviewUrl(compressedDataUrl);
    } catch (err) {
      alert("Erro ao processar imagem. Tente outro arquivo.");
      setPreviewUrl(null);
    } finally {
      setIsCompressing(false);
    }
  }

  function handleOpenUpload() {
    setPreviewUrl(null);
    setPhotoType("BEFORE");
    setProcedureId(filterProcedureId !== "ALL" ? filterProcedureId : "");
    setCaption("");
    setCapturedAt(new Date().toISOString().slice(0, 10));
    setAuthorizedSocialMedia(false);
    setIsUploadOpen(true);
  }

  async function handleSavePhoto(e: React.FormEvent) {
    e.preventDefault();
    if (!previewUrl) {
      alert("Selecione ou tire uma foto antes de salvar.");
      return;
    }

    try {
      await createPhotoMutation.mutateAsync({
        photo_type: photoType,
        procedure_id: procedureId || null,
        image_url: previewUrl,
        caption: caption.trim() || null,
        captured_at: new Date(capturedAt).toISOString(),
        authorized_social_media: authorizedSocialMedia,
      });
      setIsUploadOpen(false);
    } catch (err) {
      alert("Não foi possível salvar a foto. Tente novamente.");
    }
  }

  async function handleDelete(photo: PatientPhoto) {
    const confirmMsg = `Deseja realmente excluir esta foto (${photo.photo_type === "BEFORE" ? "Antes" : photo.photo_type === "AFTER" ? "Depois" : "Geral"})?`;
    if (confirm(confirmMsg)) {
      try {
        await deletePhotoMutation.mutateAsync(photo.id);
        if (lightboxPhoto?.id === photo.id) {
          setLightboxPhoto(null);
        }
      } catch (err) {
        alert("Erro ao excluir foto.");
      }
    }
  }

  function formatDate(dateStr: string) {
    try {
      return new Date(dateStr).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  }

  return (
    <div className={styles.container}>
      {/* Barra de Controle Superior */}
      <div className={styles.topBar}>
        <div className={styles.viewToggle}>
          <button
            type="button"
            className={`${styles.toggleBtn} ${
              viewMode === "grid" ? styles.toggleBtnActive : ""
            }`}
            onClick={() => setViewMode("grid")}
          >
            🖼️ Galeria ({photos.length})
          </button>
          <button
            type="button"
            className={`${styles.toggleBtn} ${
              viewMode === "compare" ? styles.toggleBtnActive : ""
            }`}
            onClick={() => setViewMode("compare")}
          >
            ⚖️ Comparador Antes & Depois
          </button>
        </div>

        <div className={styles.filtersGroup}>
          <select
            className={styles.filterSelect}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as PhotoType | "ALL")}
            aria-label="Filtrar por tipo de foto"
          >
            <option value="ALL">Todos os Tipos</option>
            <option value="BEFORE">Apenas Antes</option>
            <option value="AFTER">Apenas Depois</option>
            <option value="GENERAL">Acompanhamento Geral</option>
          </select>

          <select
            className={styles.filterSelect}
            value={filterProcedureId}
            onChange={(e) => setFilterProcedureId(e.target.value)}
            aria-label="Filtrar por procedimento"
          >
            <option value="ALL">Todos os Procedimentos</option>
            {procedures.map((proc) => (
              <option key={proc.id} value={proc.id}>
                {proc.name}
              </option>
            ))}
          </select>

          <button
            type="button"
            className={styles.primaryActionBtn}
            onClick={handleOpenUpload}
          >
            📷 + Nova Foto
          </button>
        </div>
      </div>

      {/* Conteúdo: Grade de Fotos */}
      {viewMode === "grid" && (
        <>
          {photos.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📷</div>
              <h3>Nenhuma foto registrada ainda</h3>
              <p>
                Acompanhe visualmente a evolução estética de {patientName}.
                Fotografe o "Antes" para documentar o ponto de partida do
                tratamento e comprovar os resultados!
              </p>
              <button
                type="button"
                className={styles.primaryActionBtn}
                onClick={handleOpenUpload}
              >
                + Anexar ou Tirar Primeira Foto
              </button>
            </div>
          ) : (
            <div className={styles.photoGrid}>
              {photos.map((photo) => (
                <div key={photo.id} className={styles.photoCard}>
                  <div
                    className={styles.imageWrapper}
                    onClick={() => setLightboxPhoto(photo)}
                    title="Clique para ampliar"
                  >
                    <img
                      src={photo.image_url}
                      alt={photo.caption || "Registro clínico"}
                      className={styles.photoImg}
                      loading="lazy"
                    />
                    <span
                      className={`${styles.badgeType} ${
                        photo.photo_type === "BEFORE"
                          ? styles.badgeBefore
                          : photo.photo_type === "AFTER"
                          ? styles.badgeAfter
                          : styles.badgeGeneral
                      }`}
                    >
                      {photo.photo_type === "BEFORE"
                        ? "Antes"
                        : photo.photo_type === "AFTER"
                        ? "Depois"
                        : "Geral"}
                    </span>
                    {photo.authorized_social_media && (
                      <span className={styles.badgeLgpd} title="Uso em redes autorizado pela paciente">
                        ✨ Redes OK
                      </span>
                    )}
                  </div>

                  <div className={styles.cardBody}>
                    {photo.procedure_name && (
                      <span className={styles.procedureTag}>
                        {photo.procedure_name}
                      </span>
                    )}
                    <p className={styles.captionText}>
                      {photo.caption || <em>Sem legenda</em>}
                    </p>
                    <div className={styles.dateFooter}>
                      <span>📅 {formatDate(photo.captured_at)}</span>
                      <button
                        type="button"
                        className={styles.deleteBtn}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(photo);
                        }}
                        title="Excluir foto"
                      >
                        Excluir
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Conteúdo: Modo Comparador Lado a Lado */}
      {viewMode === "compare" && (
        <div className={styles.comparatorContainer}>
          <div className={styles.comparatorHeader}>
            <div>
              <h3 style={{ margin: 0 }}>Comparador Clínico: Antes x Depois</h3>
              <p style={{ margin: "4px 0 0", color: "var(--text-muted)", fontSize: "0.875rem" }}>
                Selecione as fotos para colocar lado a lado e evidenciar a transformação.
              </p>
            </div>
            {diffDays !== null && (
              <span className={styles.diffTimeTag}>
                ⏱️ Intervalo de {diffDays} {diffDays === 1 ? "dia" : "dias"} entre as fotos
              </span>
            )}
          </div>

          <div className={styles.comparatorGrid}>
            {/* Lado do Antes */}
            <div className={styles.comparatorSide}>
              <div className={styles.sideHeader}>
                <strong style={{ color: "#2563eb" }}>🔵 PONTO DE PARTIDA (ANTES)</strong>
                <select
                  className={styles.filterSelect}
                  value={selectedBefore?.id || ""}
                  onChange={(e) => setCompareBeforeId(e.target.value)}
                >
                  <option value="">Selecione uma foto do Antes...</option>
                  {beforePhotos.map((p) => (
                    <option key={p.id} value={p.id}>
                      {formatDate(p.captured_at)} - {p.procedure_name || "Sem proced."} ({p.caption || "Sem nota"})
                    </option>
                  ))}
                </select>
              </div>
              <div className={styles.comparatorImgBox}>
                {selectedBefore ? (
                  <img
                    src={selectedBefore.image_url}
                    alt="Foto do Antes"
                    className={styles.comparatorImg}
                    onClick={() => setLightboxPhoto(selectedBefore)}
                    style={{ cursor: "pointer" }}
                  />
                ) : (
                  <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "1rem" }}>
                    Nenhuma foto marcada como "Antes" disponível.
                  </p>
                )}
              </div>
              {selectedBefore && (
                <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  <strong>Data:</strong> {formatDate(selectedBefore.captured_at)}
                  {selectedBefore.caption && <span> • {selectedBefore.caption}</span>}
                </div>
              )}
            </div>

            {/* Lado do Depois */}
            <div className={styles.comparatorSide}>
              <div className={styles.sideHeader}>
                <strong style={{ color: "var(--success)" }}>🟢 RESULTADO ALCANÇADO (DEPOIS)</strong>
                <select
                  className={styles.filterSelect}
                  value={selectedAfter?.id || ""}
                  onChange={(e) => setCompareAfterId(e.target.value)}
                >
                  <option value="">Selecione uma foto do Depois...</option>
                  {afterPhotos.map((p) => (
                    <option key={p.id} value={p.id}>
                      {formatDate(p.captured_at)} - {p.procedure_name || "Sem proced."} ({p.caption || "Sem nota"})
                    </option>
                  ))}
                </select>
              </div>
              <div className={styles.comparatorImgBox}>
                {selectedAfter ? (
                  <img
                    src={selectedAfter.image_url}
                    alt="Foto do Depois"
                    className={styles.comparatorImg}
                    onClick={() => setLightboxPhoto(selectedAfter)}
                    style={{ cursor: "pointer" }}
                  />
                ) : (
                  <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "1rem" }}>
                    Nenhuma foto marcada como "Depois" disponível.
                  </p>
                )}
              </div>
              {selectedAfter && (
                <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  <strong>Data:</strong> {formatDate(selectedAfter.captured_at)}
                  {selectedAfter.caption && <span> • {selectedAfter.caption}</span>}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal de Upload / Captura de Foto */}
      {isUploadOpen && (
        <div className={styles.modalBackdrop} onClick={() => setIsUploadOpen(false)}>
          <div
            className={styles.modalContent}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Nova Foto de Evolução"
          >
            <h2 className={styles.modalTitle}>📷 Registrar Foto de Evolução</h2>

            <form onSubmit={handleSavePhoto} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {/* Seletor de Arquivo ou Câmera */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                style={{ display: "none" }}
                onChange={handleFileSelect}
              />

              {!previewUrl ? (
                <div
                  className={styles.uploadArea}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div style={{ fontSize: "2rem" }}>📸</div>
                  <strong>Tirar foto com o celular ou escolher da galeria</strong>
                  <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                    {isCompressing ? "Processando imagem..." : "Formatos: JPG, PNG, WEBP. Compressão automática."}
                  </span>
                </div>
              ) : (
                <div className={styles.previewBox}>
                  <img src={previewUrl} alt="Preview" className={styles.previewImg} />
                  <button
                    type="button"
                    className={styles.removePreviewBtn}
                    onClick={() => {
                      setPreviewUrl(null);
                    }}
                    title="Trocar foto"
                  >
                    ✕
                  </button>
                </div>
              )}

              {/* Classificação da Foto */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Etapa / Tipo de Foto *</label>
                <select
                  className={styles.formSelect}
                  value={photoType}
                  onChange={(e) => setPhotoType(e.target.value as PhotoType)}
                  required
                >
                  <option value="BEFORE">🔵 Antes (Ponto de Partida)</option>
                  <option value="AFTER">🟢 Depois (Resultado Alcançado)</option>
                  <option value="GENERAL">⚪ Acompanhamento Geral</option>
                </select>
              </div>

              {/* Procedimento Vinculado */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Procedimento Relacionado</label>
                <select
                  className={styles.formSelect}
                  value={procedureId}
                  onChange={(e) => setProcedureId(e.target.value)}
                >
                  <option value="">Geral / Sem procedimento específico</option>
                  {procedures.map((proc) => (
                    <option key={proc.id} value={proc.id}>
                      {proc.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Data da Foto */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Data do Registro</label>
                <input
                  type="date"
                  className={styles.formInput}
                  value={capturedAt}
                  onChange={(e) => setCapturedAt(e.target.value)}
                  required
                />
              </div>

              {/* Legenda / Anotação */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Legenda ou Observação Clínica</label>
                <textarea
                  className={styles.formTextarea}
                  placeholder="Ex: 1ª sessão de microagulhamento, foco em cicatriz de acne..."
                  value={caption}
                  onChange={(e) => setCaption(e.target.value)}
                  maxLength={255}
                />
              </div>

              {/* Consentimento LGPD Redes Sociais */}
              <label className={styles.checkboxCard}>
                <input
                  type="checkbox"
                  checked={authorizedSocialMedia}
                  onChange={(e) => setAuthorizedSocialMedia(e.target.checked)}
                />
                <span className={styles.checkboxText}>
                  <strong>Autorização de Imagem (LGPD):</strong> A paciente autorizou
                  o uso anônimo desta foto para divulgação em redes sociais ou portfólio.
                </span>
              </label>

              <div className={styles.modalActions}>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() => setIsUploadOpen(false)}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="button button--primary"
                  disabled={!previewUrl || createPhotoMutation.isPending}
                >
                  {createPhotoMutation.isPending ? "Salvando..." : "Salvar Foto"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lightbox / Tela Cheia */}
      {lightboxPhoto && (
        <div
          className={styles.lightboxBackdrop}
          onClick={() => setLightboxPhoto(null)}
        >
          <button
            type="button"
            className={styles.lightboxCloseBtn}
            onClick={() => setLightboxPhoto(null)}
            title="Fechar"
          >
            ✕
          </button>
          <img
            src={lightboxPhoto.image_url}
            alt={lightboxPhoto.caption || "Foto ampliada"}
            className={styles.lightboxImg}
            onClick={(e) => e.stopPropagation()}
          />
          <div className={styles.lightboxMeta} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 4px" }}>
              {lightboxPhoto.photo_type === "BEFORE"
                ? "🔵 Foto do Antes"
                : lightboxPhoto.photo_type === "AFTER"
                ? "🟢 Foto do Depois"
                : "⚪ Acompanhamento Geral"}
              {lightboxPhoto.procedure_name && ` — ${lightboxPhoto.procedure_name}`}
            </h3>
            {lightboxPhoto.caption && <p style={{ margin: "4px 0" }}>{lightboxPhoto.caption}</p>}
            <p style={{ margin: 0, fontSize: "0.8125rem", opacity: 0.8 }}>
              Registrada em {formatDate(lightboxPhoto.captured_at)}
              {lightboxPhoto.authorized_social_media && " • ✨ Divulgação autorizada"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
