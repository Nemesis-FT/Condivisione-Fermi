import React from "react";
import Style from "./NotFound.module.css";
import {useTranslation} from "react-i18next";
import {Button} from "@steffo/bluelib-react";
import {useHistory} from "react-router-dom";

export default function NotFound() {
    let {t} = useTranslation()
    let h = useHistory()
    return (
        <div className={Style.NotFound}>
            <h1>404</h1>
            <h2>{t("not_found.message1")}</h2>
            <h3>{t("not_found.message2")}</h3>
            <Button onClick={e =>{h.push("/")}}>{t("not_found.message3")}</Button>
        </div>
    );
}