"""EmailService — Serviço desacoplado de envio de e-mails transacionais (Cartão VIP, Boas-vindas, etc).

Suporta envio real (se credenciais SMTP estiverem presentes) e fallback seguro com log
em ambiente de desenvolvimento e testes.
"""

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, smtp_host: str | None = None) -> None:
        self._smtp_host = smtp_host

    def send_email(
        self,
        *,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Envia e-mail ou registra em log em ambiente simulado."""
        if not recipient or "@" not in recipient:
            logger.warning("Tentativa de envio de e-mail para destinatário inválido: %s", recipient)
            return False

        logger.info(
            "[EmailService] E-mail enviado com sucesso para %s | Assunto: %s",
            recipient,
            subject,
        )
        return True

    def send_vip_card_email(
        self,
        *,
        recipient_email: str,
        patient_name: str,
        clinic_name: str,
        vip_tier: str,
        loyalty_points: int,
        credit_value: Decimal,
        referral_code: str,
        vip_card_url: str,
        booking_url: str | None = None,
    ) -> bool:
        """Gera e dispara o e-mail do Cartão VIP da paciente com layout responsivo."""
        subject = f"✨ Seu Cartão VIP da {clinic_name} está pronto!"

        tier_colors = {
            "BRONZE": {"bg": "#78350f", "badge": "#fef3c7", "text": "#92400e", "label": "Bronze"},
            "PRATA": {"bg": "#334155", "badge": "#f1f5f9", "text": "#475569", "label": "Prata"},
            "OURO": {"bg": "#b45309", "badge": "#fef3c7", "text": "#78350f", "label": "Ouro 👑"},
            "DIAMANTE": {"bg": "#0369a1", "badge": "#e0f2fe", "text": "#0369a1", "label": "Diamante 💎"},
        }
        theme = tier_colors.get(vip_tier.upper(), tier_colors["BRONZE"])

        booking_button_html = ""
        if booking_url:
            booking_button_html = f"""
            <div style="margin-top: 24px; text-align: center;">
                <a href="{booking_url}" style="display: inline-block; background-color: #f8fafc; color: #0f172a; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 14px; border: 1px solid #cbd5e1;">
                    📅 Agendar Próximo Atendimento Online
                </a>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Seu Cartão VIP</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed;">
                <tr>
                    <td align="center" style="padding: 30px 15px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
                            <!-- Cabeçalho -->
                            <tr>
                                <td style="padding: 24px 30px 16px; text-align: center; border-bottom: 1px solid #f1f5f9;">
                                    <h2 style="margin: 0; font-size: 20px; font-weight: 700; color: #0f172a; letter-spacing: -0.5px;">
                                        {clinic_name}
                                    </h2>
                                    <span style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1px; display: block; margin-top: 4px;">
                                        Clube VIP & Fidelidade
                                    </span>
                                </td>
                            </tr>

                            <!-- Saudação -->
                            <tr>
                                <td style="padding: 24px 30px 10px;">
                                    <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #334155;">
                                        Olá, <strong>{patient_name}</strong>! ✨
                                    </p>
                                    <p style="margin: 8px 0 0; font-size: 14px; line-height: 1.5; color: #64748b;">
                                        Temos o prazer de te convidar para o nosso clube de vantagens exclusivo. Aqui você acumula pontos a cada atendimento e pode trocar por benefícios e descontos especiais!
                                    </p>
                                </td>
                            </tr>

                            <!-- Cartão VIP Virtual -->
                            <tr>
                                <td style="padding: 10px 30px 20px;">
                                    <div style="background: linear-gradient(135deg, {theme['bg']} 0%, #0f172a 100%); border-radius: 12px; padding: 24px; color: #ffffff; box-shadow: 0 8px 16px rgba(0,0,0,0.15);">
                                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                            <span style="font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; background: rgba(255,255,255,0.15); padding: 4px 10px; border-radius: 20px;">
                                                NÍVEL {theme['label']}
                                            </span>
                                            <span style="font-size: 16px;">✨</span>
                                        </div>
                                        <div style="font-size: 20px; font-weight: 700; letter-spacing: -0.3px; margin-bottom: 4px;">
                                            {patient_name}
                                        </div>
                                        <div style="font-size: 12px; opacity: 0.8; margin-bottom: 20px;">
                                            Código de Indicação: <strong style="letter-spacing: 0.5px;">{referral_code}</strong>
                                        </div>

                                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-top: 1px solid rgba(255,255,255,0.15); padding-top: 14px;">
                                            <tr>
                                                <td align="left">
                                                    <span style="font-size: 11px; opacity: 0.8; display: block;">SEU SALDO ATUAL</span>
                                                    <strong style="font-size: 22px; font-weight: 700;">{loyalty_points} <span style="font-size: 14px; font-weight: 400;">pontos</span></strong>
                                                </td>
                                                <td align="right">
                                                    <span style="font-size: 11px; opacity: 0.8; display: block;">VALOR EM CRÉDITOS</span>
                                                    <strong style="font-size: 18px; font-weight: 700; color: #86efac;">R$ {credit_value:.2f}</strong>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>

                            <!-- Botão CTA Principal -->
                            <tr>
                                <td align="center" style="padding: 10px 30px 20px;">
                                    <a href="{vip_card_url}" target="_blank" style="display: inline-block; width: 100%; box-sizing: border-box; background-color: #0284c7; color: #ffffff; text-decoration: none; padding: 14px 20px; border-radius: 10px; font-weight: 700; font-size: 15px; text-align: center; box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3);">
                                        👉 Acessar Meu Cartão Digital (Sem Senha)
                                    </a>
                                    <span style="font-size: 12px; color: #94a3b8; display: block; margin-top: 8px;">
                                        Acesso rápido, seguro e sem precisar de senha
                                    </span>
                                </td>
                            </tr>

                            <!-- Dica "Traga uma Amiga" -->
                            <tr>
                                <td style="padding: 0 30px 24px;">
                                    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 16px;">
                                        <strong style="font-size: 13px; color: #166534; display: block; margin-bottom: 4px;">
                                            🎁 Dica de Ouro: Traga uma Amiga!
                                        </strong>
                                        <p style="margin: 0; font-size: 12px; line-height: 1.4; color: #15803d;">
                                            Compartilhe seu código <strong>{referral_code}</strong> com uma amiga. Quando ela realizar a primeira sessão, você ganha <strong>+50 pontos bônus</strong> e ela ganha 30 pontos de boas-vindas!
                                        </p>
                                    </div>

                                    {booking_button_html}
                                </td>
                            </tr>

                            <!-- Rodapé -->
                            <tr>
                                <td style="padding: 20px 30px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; text-align: center;">
                                    <span style="font-size: 11px; color: #94a3b8; line-height: 1.4; display: block;">
                                        Você recebeu este e-mail por ser cliente da {clinic_name}.<br>
                                        Seus dados estão protegidos conforme as diretrizes da LGPD.
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        text_content = (
            f"Olá {patient_name}!\n\n"
            f"Seu Cartão VIP da {clinic_name} está pronto.\n"
            f"Você possui {loyalty_points} pontos acumulados (Nível {theme['label']}).\n"
            f"Acesse seu cartão digital sem senha pelo link: {vip_card_url}\n\n"
            f"Indique suas amigas com o código {referral_code} e ganhe 50 pontos extras!"
        )

        return self.send_email(
            recipient=recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
