function updatePortField(
    port,
    field,
    value
){

    let existing =
        odfState.ports.find(
            p=>p.port===port
        );

    if(!existing){

        existing = {

            port:port,

            olt:"",

            pon:"",

            feederCable:"",

            buffer:"",

            strand:"",

            destinationClosure:"",

            description:""
        };

        odfState.ports.push(
            existing
        );
    }

   existing[field] = value;

if(field==="feederCable"){

    const cable =
        getCableInfo(value);

    if(cable){

        existing.destinationClosure =

            cable.destinationClosure || "";
    }
}

renderODF();

}

async function saveODF(){

    const response =
        await fetch(

            window.location.pathname
            .replace(
                "/edit",
                "/save"
            ),

            {

                method:"POST",

                headers:{
                    "Content-Type":
                    "application/json"
                },

                body:JSON.stringify(
                    odfState
                )
            }
        );

    const result =
        await response.json();

    if(result.success){

        alert("Saved");
    }
}

function getCableInfo(
    cableName
){

    return cableRegistry.find(
        c=>c.cableName===cableName
    );
}


function renderODF(){

    let html = `

        <div style="
    margin-bottom:12px;
">

<button
onclick="
    saveODF()
">

Save ODF

</button>

</div>

    <div class="card">

    <table>

    <thead>

    <tr>

        <th>Port</th>

        <th>OLT</th>

        <th>PON</th>

        <th>Feeder Cable</th>

        <th>Buffer</th>

        <th>Strand</th>

        <th>Destination</th>

        <th>Description</th>

    </tr>

    </thead>

    <tbody>
    `;

    for(let p=1;p<=odfState.totalPorts;p++){

        const existing =
            odfState.ports.find(
                x=>x.port===p
            ) || {};

        html += `

        <tr>

            <td>${p}</td>

            <td>

                <input

value="${
    existing.olt || ""
}"

onchange="
    updatePortField(
        ${p},
        'olt',
        this.value
    )
">

            </td>

            <td>

               <input

value="${
    existing.pon || ""
}"

onchange="
    updatePortField(
        ${p},
        'pon',
        this.value
    )
">

            </td>

            <td>

                <select

onchange="
    updatePortField(
        ${p},
        'feederCable',
        this.value
    )
">

<option value="">
    Select Cable
</option>

${
    cableRegistry
.filter(
    cable=>

        cable.role==="feeder" ||

        cable.role==="through"
)
.map(
        cable=>`

<option

value="${cable.cableName}"

${
    existing.feederCable ===
    cable.cableName

    ? "selected"

    : ""
}>

${cable.cableName}

(${cable.size}F)

</option>
`
    ).join("")
}

</select>

            </td>

            <td>

               <input

value="${
    existing.buffer || ""
}"

onchange="
    updatePortField(
        ${p},
        'buffer',
        this.value
    )
">

            </td>

            <td>

               <input

value="${
    existing.strand || ""
}"

onchange="
    updatePortField(
        ${p},
        'strand',
        this.value
    )
">

            </td>

            <td>

                <input

value="${
    existing.destinationClosure || ""
}"

onchange="
    updatePortField(
        ${p},
        'destinationClosure',
        this.value
    )
">

            </td>

            <td>

               <input

value="${
    existing.description || ""
}"

onchange="
    updatePortField(
        ${p},
        'description',
        this.value
    )
">

            </td>

        </tr>
        `;
    }

    html += `
    </tbody>
    </table>
    </div>
    `;

    document.getElementById(
        "workspace"
    ).innerHTML = html;
}

renderODF();
