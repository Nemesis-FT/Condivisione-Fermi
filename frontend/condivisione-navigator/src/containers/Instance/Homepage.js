import React, {useEffect, useState} from "react";
import Style from "./Homepage.module.css";
import {Anchor, Box, Button, Chapter, Details, Dialog, Heading, Panel} from "@steffo/bluelib-react";
import {useAppContext} from "../../libs/Context";
import {useHistory, useParams} from "react-router-dom";
import {faBackward, faDoorClosed, faStar} from "@fortawesome/free-solid-svg-icons";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome'
import schema from "../config";
import Login from "./Login.js";
import Register from "./Register";
import {useTranslation} from "react-i18next";


export default function Home() {
    const {url} = useParams();
    const {instanceIp, setInstanceIp} = useAppContext()
    const {instance, setInstanceData} = useAppContext()
    const {connected, setConnected} = useAppContext()
    const [server, setServer] = useState(null)
    const [showInfo, setShowInfo] = useState(false)
    const [isFav, setIsFav] = useState(false)
    const [channelLink, setChannelLink] = useState("null")
    let history = useHistory();
    let { t } = useTranslation()

    useEffect(() => {
        if (instanceIp !== url) {
            setInstanceIp(url)
            setConnected(true)
            localStorage.setItem("instanceIp", url);
        }
    })

    useEffect(() => {
        if (server) {
            let el = {name: server.server.name, address: instanceIp, university: server.server.university}
            if (localStorage.getItem("favs")) {
                let favs = JSON.parse(localStorage.getItem("favs"))
                let addresses = favs.map(f => {
                    return f.address
                })
                if (addresses.includes(instanceIp)) {
                    console.debug("subs")
                    setIsFav(true)
                }
            }
        }
    }, [server])

    useEffect(() => {
        gather_data()
    }, [connected])

    async function gather_data() {
        const response = await fetch(schema + url + "/server/planetarium", {
            method: "GET",
            credentials: "include",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': process.env.DOMAIN
            },
        });
        if (response.status === 200) {
            let values = await response.json()
            console.debug(values)
            setServer(values)
            console.debug(server)
            setInstanceData(values.server)
        }
    }

    async function disconnect() {
        setInstanceIp(null);
        setConnected(false);
        localStorage.removeItem("instanceIp");
        history.push("/")
    }

    async function addFav() {
        let el = {name: server.server.name, address: instanceIp, school: server.server.school}
        if (localStorage.getItem("favs")) {
            console.debug("Favs are present!")
            let favs = JSON.parse(localStorage.getItem("favs"))
            let addresses = favs.map(f => {
                return f.address
            })
            if (addresses.includes(instanceIp)) {
                return;
            }
            favs.push(el)
            localStorage.setItem("favs", JSON.stringify(favs))
            console.debug(localStorage.getItem("favs"))
        } else {
            localStorage.setItem("favs", JSON.stringify([el,]))
        }
        setIsFav(true)
    }

    return (
        <div>
            {server ? (
                <div className={Style.Home}>
                    <div className={Style.lander}>
                        <Heading level={1}>{server.server.name}

                        </Heading>
                        <p className="text-muted">{server.server.school} </p>
                    </div>
                    <Dialog>{t("login_page.message")}</Dialog>
                    <Chapter>
                        {!isFav ? (
                        <div>
                            <Button onClick={e => addFav()}><FontAwesomeIcon
                                icon={faStar}/> </Button>
                        </div>) : (<div/>)}

                            <Button onClick={e => disconnect()}><FontAwesomeIcon icon={faDoorClosed}/></Button>

                    </Chapter>
                    <Login/>
                    <Details summary={"Register"}>
                        <Register/>
                    </Details>
                </div>

            ) : (
                <Panel>Collegamento in corso...</Panel>
            )}
        </div>
    );
}