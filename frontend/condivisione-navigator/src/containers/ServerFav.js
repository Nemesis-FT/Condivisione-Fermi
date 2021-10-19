import React from "react";
import {Anchor, Button, Chapter, Panel} from "@steffo/bluelib-react";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome'
import {faTrash} from "@fortawesome/free-solid-svg-icons";

export default function ServerFav(props) {

    async function remove() {
        let res = props.favList
        res = props.favList.filter(function (element) {
            return element.address !== props.fav.address
        })
        props.setFav(res)
        localStorage.setItem("favs", JSON.stringify(res))
    }

    return (
        <Panel>
            <Chapter>
                <div><Anchor href={"/srv/" + props.fav.address}>{props.fav.name}</Anchor><br/>({props.fav.university})</div>
                <Button onClick={e => remove()}><FontAwesomeIcon icon={faTrash}/></Button>
            </Chapter>
        </Panel>
    );
}