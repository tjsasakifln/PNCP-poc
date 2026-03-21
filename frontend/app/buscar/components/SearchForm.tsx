"use client";

import { UF_NAMES } from "../../../lib/constants/uf-names";
import { dateDiffInDays } from "../../../lib/utils/dateDiffInDays";
import SearchFormHeader from "./SearchFormHeader";
import SearchFormActions from "./SearchFormActions";
import SearchCustomizePanel from "./SearchCustomizePanel";

export type { SearchFormProps } from "./SearchForm.types";
import type { SearchFormProps } from "./SearchForm.types";

export default function SearchForm(props: SearchFormProps) {
  const {
    ufsSelecionadas, status, modalidades, modoBusca, dataInicial, dataFinal,
  } = props;

  const compactSummary = (() => {
    const parts: string[] = [];
    if (ufsSelecionadas.size === 27) {
      parts.push('Todo o Brasil');
    } else if (ufsSelecionadas.size === 1) {
      const uf = Array.from(ufsSelecionadas)[0];
      parts.push(UF_NAMES[uf] || uf);
    } else {
      parts.push(`${ufsSelecionadas.size} estados`);
    }
    const statusLabels: Record<string, string> = {
      recebendo_proposta: 'Abertas',
      em_julgamento: 'Em julgamento',
      encerrada: 'Encerradas',
      todos: 'Todos os status',
    };
    parts.push(statusLabels[status] || 'Abertas');
    if (modalidades.length > 0) {
      parts.push(`${modalidades.length} modalidade${modalidades.length !== 1 ? 's' : ''}`);
    }
    if (modoBusca === 'abertas') {
      parts.push("Oportunidades recentes");
    } else if (dataInicial && dataFinal) {
      const days = dateDiffInDays(dataInicial, dataFinal);
      parts.push(`${days} dia${days !== 1 ? 's' : ''}`);
    }
    return parts.join(' • ');
  })();

  return (
    <div role="search" aria-label="Buscar licitações">
      <SearchFormHeader
        setores={props.setores}
        setoresLoading={props.setoresLoading}
        setoresError={props.setoresError}
        setoresUsingFallback={props.setoresUsingFallback}
        setoresUsingStaleCache={props.setoresUsingStaleCache}
        staleCacheAge={props.staleCacheAge}
        setoresRetryCount={props.setoresRetryCount}
        setorId={props.setorId}
        setSetorId={props.setSetorId}
        fetchSetores={props.fetchSetores}
        searchMode={props.searchMode}
        setSearchMode={props.setSearchMode}
        termosArray={props.termosArray}
        termoInput={props.termoInput}
        setTermoInput={props.setTermoInput}
        termValidation={props.termValidation}
        addTerms={props.addTerms}
        removeTerm={props.removeTerm}
        clearResult={props.clearResult}
        showFirstUseTip={props.showFirstUseTip}
        onDismissFirstUseTip={props.onDismissFirstUseTip}
      />
      <SearchFormActions
        loading={props.loading}
        buscar={props.buscar}
        searchButtonRef={props.searchButtonRef}
        canSearch={props.canSearch}
        searchLabel={props.searchLabel}
        searchMode={props.searchMode}
        termValidation={props.termValidation}
        result={props.result}
        handleSaveSearch={props.handleSaveSearch}
        isMaxCapacity={props.isMaxCapacity}
        isTrialExpired={props.isTrialExpired}
        isGracePeriod={props.isGracePeriod}
      />
      <SearchCustomizePanel
        customizeOpen={props.customizeOpen}
        setCustomizeOpen={props.setCustomizeOpen}
        ufsSelecionadas={props.ufsSelecionadas}
        toggleUf={props.toggleUf}
        toggleRegion={props.toggleRegion}
        selecionarTodos={props.selecionarTodos}
        limparSelecao={props.limparSelecao}
        dataInicial={props.dataInicial}
        setDataInicial={props.setDataInicial}
        dataFinal={props.dataFinal}
        setDataFinal={props.setDataFinal}
        modoBusca={props.modoBusca}
        dateLabel={props.dateLabel}
        locationFiltersOpen={props.locationFiltersOpen}
        setLocationFiltersOpen={props.setLocationFiltersOpen}
        advancedFiltersOpen={props.advancedFiltersOpen}
        setAdvancedFiltersOpen={props.setAdvancedFiltersOpen}
        esferas={props.esferas}
        setEsferas={props.setEsferas}
        municipios={props.municipios}
        setMunicipios={props.setMunicipios}
        status={props.status}
        setStatus={props.setStatus}
        modalidades={props.modalidades}
        setModalidades={props.setModalidades}
        valorMin={props.valorMin}
        setValorMin={props.setValorMin}
        valorMax={props.valorMax}
        setValorMax={props.setValorMax}
        setValorValid={props.setValorValid}
        validationErrors={props.validationErrors}
        loading={props.loading}
        clearResult={props.clearResult}
        planInfo={props.planInfo}
        onShowUpgradeModal={props.onShowUpgradeModal}
        compactSummary={compactSummary}
      />
    </div>
  );
}
