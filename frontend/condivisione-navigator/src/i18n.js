import i18n from 'i18next';
import {initReactI18next} from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        debug: true,
        fallbackLng: 'en',
        interpolation: {
            escapeValue: false,
        },
        resources: {
            en: {
                translation: {
                    footer: {
                        line1: "Condivisione and Condivisione-Navigator are constellation software created by Fermitech Softworks based on Gestione.",
                        line2: "Condivisione-Navigator uses",
                        line3: "developed by Steffo."
                    },
                    descriptions: {
                        line1: "Condivisione is the webapp that allows schools to coordinate free lessons among their students.",
                        blob: "The navigator allows you to explore the constellation of Consivisione instances, that belong to different schools. To connect, enter the Condivisione url of your school, or visit it directly. It is possible to add a Condivisione instance to the official constellation, hosted by the 'Planetarium' service."
                    },
                    buttons: {
                        connect: "Connect",
                        disconnect: "Disconnect",
                        login: "Login"
                    },
                    form_names: {
                        instance_address: "Instance address"
                    },
                    status_msgs: {
                        checking: "Checking..."
                    }
                }
            },
            it: {
                translation: {
                    footer: {
                        line1: "Condivisione e Condivisione-Navigator sono software a costellazione di Fermitech Softworks basati su Gestione.",
                        line2: "Condivisione-Navigator usa",
                        line3: "sviluppata da Steffo."
                    },
                    descriptions: {
                        line1: "Condivisione è la webapp che consente alle scuole di organizzare ripetizioni tra pari, gratuitamente.",
                        blob: "Il navigatore consente di esplorare la costellazione di istanze di Condivisione appartenenti a scuole diverse. Per collegarti, inserisci l'URL dell'istanza del tuo istituto, o visita direttamente quell'indirizzo. E' possibile aggiungere l'istanza alla costellazione ufficiale, accessibile tramite il servizio 'Planetario'."
                    },
                    buttons: {
                        connect: "Connettiti",
                        disconnect: "Disconnettiti",
                        login: "Login"
                    },
                    form_names: {
                        instance_address: "Indirizzo istanza"
                    },
                    status_msgs: {
                        checking: "Verifica..."
                    }
                }
            }
        }
    });

export default i18n;