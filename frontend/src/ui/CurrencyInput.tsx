import { useEffect, useState } from "react";
import { centsToDisplay, centsToMoney, digitsToCents, moneyToCents } from "@/lib/money/parse";
import type { Money } from "@/lib/money/money";

type Props = {
  id?: string;
  value: Money | "";
  onChange: (value: Money) => void;
  "aria-label"?: string;
  autoFocus?: boolean;
};

/**
 * Máscara de moeda: usuária só digita dígitos, sempre em centavos —
 * nunca deixa o cursor num decimal ambíguo. Ver frontend/BACKLOG.md F-014.
 */
export function CurrencyInput({ id, value, onChange, autoFocus, ...aria }: Props) {
  const [display, setDisplay] = useState(() => centsToDisplay(moneyToCents(value)));

  // Sincroniza com mudanças externas de `value` (ex: setValue() ao
  // selecionar um procedimento) — sem isto o display fica preso no
  // valor com que o input montou. Ver F-014 (autofill de preço/custo).
  useEffect(() => {
    setDisplay(centsToDisplay(moneyToCents(value)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const cents = digitsToCents(e.target.value);
    setDisplay(centsToDisplay(cents));
    onChange(centsToMoney(cents));
  }

  return (
    <div className="currency-input">
      <span className="currency-input__prefix">R$</span>
      <input
        id={id}
        inputMode="numeric"
        value={display}
        onChange={handleChange}
        autoFocus={autoFocus}
        aria-label={aria["aria-label"]}
      />
    </div>
  );
}
