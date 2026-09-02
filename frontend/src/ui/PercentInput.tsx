import { useEffect, useState } from "react";
import { centsToDisplay, centsToMoney, digitsToCents, moneyToCents } from "@/lib/money/parse";
import type { Money } from "@/lib/money/money";

type Props = {
  id?: string;
  value: Money | "";
  onChange: (value: Money) => void;
  "aria-label"?: string;
};

/**
 * Mesma máscara de dígitos do CurrencyInput (2 casas decimais), mas
 * com sufixo "%" em vez de prefixo "R$". As taxas de financial-settings
 * chegam do backend como MoneyOut (2 casas), não RateOut (4 casas) —
 * ver nota de F-012a no frontend/BACKLOG.md.
 */
export function PercentInput({ id, value, onChange, ...aria }: Props) {
  const [display, setDisplay] = useState(() => centsToDisplay(moneyToCents(value)));

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
    <div className="percent-input">
      <input
        id={id}
        inputMode="numeric"
        value={display}
        onChange={handleChange}
        aria-label={aria["aria-label"]}
      />
      <span className="percent-input__suffix">%</span>
    </div>
  );
}
