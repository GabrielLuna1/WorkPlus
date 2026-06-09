from typing import List
from core.logger import logger


SCORE_LIMIAR = 80


def notificar_vagas_imperdiveis(vagas: List[dict]) -> int:
    """Envia notificacoes do Windows para vagas com score acima do limiar.

    Args:
        vagas: Lista de dicts com pelo menos titulo, empresa, score.

    Returns:
        Numero de notificacoes enviadas.
    """
    imperdiveis = [v for v in vagas if v.get("score", 0) >= SCORE_LIMIAR]
    if not imperdiveis:
        return 0

    logger.info(
        "notification.match_supremo",
        total=len(imperdiveis),
        limiar=SCORE_LIMIAR,
    )

    enviadas = 0
    for vaga in imperdiveis:
        try:
            _enviar_toast(vaga)
            enviadas += 1
        except Exception as e:
            logger.warning("notification.erro", error=str(e))

    return enviadas


def _enviar_toast(vaga: dict) -> None:
    titulo = vaga.get("titulo", "Vaga desconhecida")
    empresa = vaga.get("empresa", "Empresa desconhecida")
    score = vaga.get("score", 0)

    try:
        from winotify import Notification, audio

        toast = Notification(
            app_id="WorkHunter",
            title=f"Match Supremo! Score: {score}",
            msg=f"{titulo} — {empresa}",
            icon=None,
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
    except ImportError:
        _enviar_toast_powershell(titulo, empresa, score)


def _enviar_toast_powershell(titulo: str, empresa: str, score: int) -> None:
    import subprocess

    ps_script = f'''
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $textNodes = $template.GetElementsByTagName("text")
    $textNodes.Item(0).AppendChild($template.CreateTextNode("Match Supremo! Score: {score}")) > $null
    $textNodes.Item(1).AppendChild($template.CreateTextNode("{titulo} — {empresa}")) > $null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("WorkHunter").Show($toast)
    '''

    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        timeout=10,
    )
