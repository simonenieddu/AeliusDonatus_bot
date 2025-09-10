3) Crea il servizio su Render
	1.	Vai su render.com → New + → Blueprint (se hai messo render.yaml)
oppure → New + → Background Worker (se vuoi farlo a mano).
	2.	Collega il repo GitHub appena creato.
	3.	Se usi Background Worker manuale, imposta:
	•	Build Command: pip install -r requirements.txt
	•	Start Command: python bot.py
	•	Environment: Python
	4.	In Environment Variables, aggiungi:
	•	TELEGRAM_BOT_TOKEN = il token di BotFather (copiato 1:1, senza apici né spazi)
	5.	Scegli il piano Free e avvia il deploy.

Nota: per il polling non serve alcun URL pubblico. Il bot parte da solo e si collega a Telegram.

⸻

4) Verifica
	•	Guarda i Logs su Render: dovresti vedere l’installazione pacchetti e poi il processo che resta avviato.
	•	Apri Telegram → @AeolusDonatus_bot → /start → prova un quiz.

⸻

FAQ rapide
	•	Serve un webhook? No, con il polling non serve. Il bot chiama Telegram periodicamente.
	•	Serve .env su Render? No, basta la variabile TELEGRAM_BOT_TOKEN impostata nella dashboard. (Puoi lasciare il codice con dotenv: se la variabile d’ambiente esiste, funziona comunque.)
	•	Render è davvero gratuito? C’è un piano free sufficiente per piccoli bot; le condizioni possono cambiare nel tempo, ma per iniziare va benissimo.
	•	Background Worker o Web Service? Per un bot in polling preferisco Background Worker: è pensato per processi senza HTTP. Se vuoi usare Webhook, invece useresti un Web Service con un endpoint.

⸻

(Opzionale) Miglioramenti per produzione
	•	Log più puliti (aggiungi logging).
	•	Comando /reload che ricarica questions.json senza redeploy.
	•	Persistenza punteggi (SQLite/MySQL) — posso fornirti schema e codice.

Se vuoi, ti preparo un repo “starter” già pronto (con render.yaml, loader JSON, logging e /reload).
