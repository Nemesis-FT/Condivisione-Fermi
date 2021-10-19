import React, {useEffect, useState} from "react";
import {Box, Button, Dialog, Form} from "@steffo/bluelib-react";
import {useAppContext} from "../libs/Context";
import {useHistory} from "react-router-dom";
import Style from "./ServerSelector.module.css"
import {faQuestionCircle} from "@fortawesome/free-solid-svg-icons";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome'
import ServerFav from "./ServerFav";
import schema from "./config";
import { useTranslation, Trans } from 'react-i18next';

export default function ServerSelector() {
    const [address, setAddress] = useState("");
    const [isValid, setIsValid] = useState(false);
    const [isChecking, setIsChecking] = useState(false);
    const [server, setServer] = useState(null);
    const {instanceIp, setInstanceIp} = useAppContext();
    const {connected, setConnected} = useAppContext();
    const [favList, setFavList] = useState([])
    const [hidden, setHidden] = useState(true)
    let history = useHistory();

    let { t } = useTranslation()


    useEffect(() => {
        conn_check()
    }, [address])

    useEffect(() => {
        if (localStorage.getItem("favs")) {
            let favs = JSON.parse(localStorage.getItem("favs"))
            setFavList(favs)
        }

    }, [connected])


    async function conn_check() {
        setIsChecking(true);
        try {
            const response = await fetch(schema + address + "/server/planetarium", {
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
                console.debug(values.server)
                setServer({
                    name: values.server.name,
                    university: values.server.school,
                    type: values.type,
                    version: values.version,
                })
                console.debug(server)
                setIsChecking(false)
                setIsValid(true)

            } else {
                setIsChecking(false);
            }
        } catch (e) {
            setIsChecking(false);
        }

    }

    async function connect() {
        if (!isValid) {
            return
        }
        setInstanceIp(address)
        localStorage.setItem("instanceIp", address)
        setConnected(true)
        console.debug("Collegamento a " + address)
        history.push("/srv/" + address)
    }

    return (
        <div>
            <Box>

                <Form>
                    <Form.Row>
                        <Form.Field onSimpleChange={e => setAddress(e)} value={address} required={true}
                                    placeholder={"condivisione.site.org"} label={t("form_names.instance_address")} validity={isValid}>
                        </Form.Field>
                    </Form.Row>
                </Form>
                <Form.Row>
                    {isChecking ? (
                        <div>{t("status_msgs.checking")}</div>
                    ) : (
                        <div></div>
                    )}

                    {isValid ? (
                        <div>
                            <Dialog bluelibClassNames={"color-lime"}>
                                {server.name} ({server.university})
                                <p> {server.type} v. {server.version} </p>
                            </Dialog>
                        </div>
                    ) : (
                        <div>

                        </div>
                    )}

                    <Button children={t("buttons.connect")} disabled={!isValid} onClick={e => connect()}>

                    </Button>
                </Form.Row>
            </Box>

            <Button onClick={(e) => {
                setHidden(!hidden)
            }}><FontAwesomeIcon icon={faQuestionCircle}/></Button>
            {hidden ? (<div></div>) : (<p>{t("descriptions.blob")}</p>)}

            <Box className={Style.Scrollable}>
                {favList ? (
                    <div>{favList.map(fav => <ServerFav fav={fav} setFav={setFavList} favList={favList}/>)}</div>
                ) : (
                    <p>Nessun server tra i preferiti. Per aggiungerne, clicca sulla stella di fianco al nome di un
                        server.</p>
                )}
            </Box>
        </div>
    );
}