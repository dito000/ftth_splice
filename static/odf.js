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

function assignBufferToODF(){

    const cable =

        document.getElementById(
            "bulkCable"
        ).value;

    const buffer =

        Number(
            document.getElementById(
                "bulkBuffer"
            ).value
        );

    const startPort =

        Number(
            document.getElementById(
                "bulkStartPort"
            ).value
        );

    if(!cable){

        alert(
            "Select a feeder cable."
        );

        return;
    }

    const endPort =
        startPort + 11;

    if(
        endPort >
        odfState.totalPorts
    ){

        alert(
            "Not enough ports available."
        );

        return;
    }

    const existingBuffer =
        odfState.ports.find(

            p =>

                p.feederCable === cable

                &&

                Number(
                    p.buffer
                ) === buffer
        );

    if(existingBuffer){

        alert(
            "That buffer is already terminated."
        );

        return;
    }

    for(
        let p=startPort;
        p<=endPort;
        p++
    ){

        const existingPort =
            odfState.ports.find(
                x=>x.port===p
            );

        if(
            existingPort &&
            existingPort.feederCable
        ){

            alert(
                "One or more ports are already occupied."
            );

            return;
        }
    }

    for(let s=1;s<=12;s++){

        const port =
            startPort + (s-1);

        let existing =
            odfState.ports.find(
                x=>x.port===port
            );

        if(!existing){

            existing = {
                port:port
            };

            odfState.ports.push(
                existing
            );
        }

        existing.feederCable =
            cable;

        existing.buffer =
            buffer;

        existing.strand =
            s;

        existing.status =
            "Assigned";
    }

    renderODF();
}

function getCableInfo(
    cableName
){

    return cableRegistry.find(
        c=>c.cableName===cableName
    );
}

function isFiberUsed(
    feederCable,
    buffer,
    strand,
    currentPort
){

    return odfState.ports.some(

        p =>

            p.port !== currentPort

            &&

            p.feederCable === feederCable

            &&

            String(
                p.buffer
            ) === String(buffer)

            &&

            String(
                p.strand
            ) === String(strand)
    );
}


function renderODF(){

    const feederCables =

        cableRegistry.filter(

            c =>

                c.role === "Feeder"

                ||

                c.role === "through"
        );

    let html = `

<div style="
    display:flex;
    gap:12px;
    align-items:center;
    margin-bottom:12px;
">

    <input

    value="${
        odfState.odfName || ""
    }"

    placeholder="
        ODF Name
    "

    onchange="
        odfState.odfName =
        this.value
    "

    style="
        font-size:18px;
        font-weight:600;
        padding:8px;
        min-width:240px;
    ">

    <input

    type="number"

    min="1"

    value="${
        odfState.totalPorts || 48
    }"

    onchange="
        odfState.totalPorts =
        parseInt(this.value);

        renderODF();
    "

    style="
        width:100px;
    ">

    <button
    onclick="
        saveODF()
    ">
        Save ODF
    </button>

</div>

 <div class="card" style="
    margin-bottom:16px;
">

<div style="
    display:flex;
    gap:12px;
    align-items:end;
    flex-wrap:wrap;
">

    <div>

        <div class="label">
            Feeder Cable
        </div>

        <select id="bulkCable">

            <option value="">
                Select Cable
            </option>

            ${
                feederCables.map(
                    c=>`

<option value="${c.cableName}">
    ${c.cableName}
</option>
`
                ).join("")
            }

        </select>

    </div>

    <div>

        <div class="label">
            Buffer
        </div>

        <select id="bulkBuffer">

            ${
                Array.from(
                    {length:24},
                    (_,i)=>`

<option value="${i+1}">
    Buffer ${i+1}
</option>
`
                ).join("")
            }

        </select>

    </div>

    <div>

        <div class="label">
            Start Port
        </div>

        <input
        id="bulkStartPort"
        type="number"
        min="1"
        value="1">

    </div>

    <button
    onclick="
        assignBufferToODF()
    ">
        Assign Buffer
    </button>

</div>

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

            const occupied =

    existing.feederCable &&

    existing.buffer &&

    existing.strand;

        html += `

     <tr class="
    ${occupied ? 'odf-port-used' : ''}
">

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

${
    isFiberUsed(
        existing.feederCable,
        existing.buffer,
        existing.strand,
        p
    )

    ? `
    <div style="
        color:#dc2626;
        font-size:11px;
        margin-top:4px;
    ">
        Fiber already assigned
    </div>
    `

    : ""
}

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
