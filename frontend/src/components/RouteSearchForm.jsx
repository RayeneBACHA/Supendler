import { useState } from "react";

function RouteSearchForm() {
    const [from, setForm] = useState("");

    return (
        <form>
            <label>
                From
                <input
                    type="text"
                    placeholder="TU Lichtwiese"
                    value={from}
                    onChange={(event) => {
                        setForm(event.target.value);
                    }}
                />
            </label>

            <p>You entered : {from}</p>

            <label>
                To
                <input
                    type="text"
                    placeholder="Darmstadt Nord"
                />
            </label>

            <label>
                Ready at
                <input
                    type="time"
                />
            </label>

            <label>
                <input type="checkbox" />
                I have a folding bike
            </label>

            <button type="submit">
                Find routes
            </button>
        </form>
    );
}

export default RouteSearchForm;