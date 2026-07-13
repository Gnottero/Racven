# Turn Piats: la web app locale del turno piatti
## Breve descrizione
Sviluppa una piccola e semplice webapp, in grado di girare su un raspberry pi e rivolta ad una piccola comunità studentesca. L'idea è quella di connettere un raspberry ad un televisore per potere mostrare alcune informazioni in tempo reale.

## Tipi di Utente
Tutti gli utenti sono caratterizzati da:
- Nome e Cognome
- Tag utente: può essere scelto dall'utente, ma deve essere univoco e nel formato @<user_tag>
- Ruolo: gli utenti possono essere normali utenti o admin
- Contribuitori: contribuiscono al turno piatti (di default è vero per tutti gli utenti)

Gli admin devono poter accedere ad una loro dashboard che mostra tutti gli utenti registrati e permette di cambiare il loro status di contributori

## Funzionalità
Tutti gli utenti devono potere mandare, dalla pagina principale, un messaggio da mostrare sullo schermo della TV come fosse una loro citazione (mostrando quindi nome utente e tag). La frase appena mandata deve essere mostrata a schermo con l'orario di invio. Deve esserci un suono di notifica quando arriva una nuova frase. Dopo un breve intervallo, il sistema deve tornare a mostrare i vari messaggi ricevuti nella giornata corrente a mo di carosello

Quando un utente lo richiede, il sistema deve mostrare, per un intervallo di tempo, la programmazione mensile del turno piatti, mettendo in evidenza chi deve svolgerlo nella giornata corrente. Il turno piatti funziona nel seguente modo:
- Ogni giorno una coppia (fissa) di membri contributori svolge il turno piatti
- La coppia ripete il turno solo dopo che tutti lo hanno svolto
- Se non è possibile formare una coppia, forma una terna, ma mai gruppi più grandi di 3 membri
- Quando un membro contribuente cambia stato, ricalcola il turno piatti del mese, riformando se necessario le coppie

## Stile grafico
Per lo stile grafico, utilizza lo stile di https://einaudi-plus.vercel.app/ 
