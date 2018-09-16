import smtplib

def sendemail(to_addr_list, subject, message, smtpserver='smtp.gmail.com:587'):
    try:
        header = 'From: %s' % from_addr
        header += 'To: %s' % ','.join(to_addr_list)
        header += 'Subject: %s' % subject
        message = header + message
        server = smtplib.SMTP(smtpserver)
        server.starttls()
        server.login(accesso, password)
        problems = server.sendmail(from_addr, to_addr_list, message)
        print(problems)
        server.quit()
        return True
    except:
        return False

chiavi = open("configurazione.txt", 'r')
dati = chiavi.readline()
appkey, telegramkey, from_addr, accesso, password, dsn, recaptcha_pubblica, recaptcha_privata, brasamail = dati.split("|",8)
email_file = open("maildump.csv", "r")
email = email_file.readline()
mail = []
mail = email.split(";")
for indirizzo in mail:
    print(indirizzo)
    successo = sendemail(indirizzo, "Chiusura account", "Gentile utente di Condivisione,\nIn vista dell'inizio di un nuovo anno scolastico, la sua utenza su Condivisione e' stata rimossa.\nPer tornare ad usufruire dei servizi di Condivisione, le sara' necessario creare una nuova utenza.\n\nGrazie per aver utilizzato Condivisione!\nQuesto messaggio è stato creato automaticamente.")
    print(successo)