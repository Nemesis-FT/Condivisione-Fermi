import React from "react";
import Style from "./Home.module.css";
import {Heading, Image, Panel} from "@steffo/bluelib-react";
import ServerSelector from "./ServerSelector";
import { useTranslation, Trans } from 'react-i18next';

export default function Home() {
    const { t } = useTranslation();
    return (
        <div className={Style.Home}>
            <div className={Style.lander}>
                <Image src={"logo.png"} width={"320px"}></Image>
                <Heading level={1}/>
                <p className="text-muted"><Trans i18nKey="descriptions.line1"></Trans></p>
            </div>
            <Panel>
                <ServerSelector/>
            </Panel>
        </div>

    );
}