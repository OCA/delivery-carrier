<html>
<head>
    <style type="text/css">
        ${css}
        .right {
            float: right;
            padding-right:50px;
        }
        .bottom {
            position: fixed
            absolute:
        }
        .small {
            font-size: 8
        }

        .valign_up, .valign_bot {
            position:absolute;
        }
        .valign_up { left:130px; }
        .valign_bot { left:200px; }

        .cadre_bottom {
            padding: 4mm;
            margin: 4mm;
            border-width: thin;
            border-style: solid;
        }

    </style>
</head>
<body>
<%page expression_filter="entity"/>
<%
def carriage_returns(text):
    return text.replace('\n', '<br />')

def carrier_name(car_type):
    return car_type.replace('_', ' ').upper()

def pick(deposit):
    return deposit.picking_ids[0]

def cpny(deposit):
    return deposit.picking_ids[0].company_id

def tabulation(text):
    return text.replace('//t', '&nbsp; &nbsp; ')

%>
<%from datetime import date %>

%for deposit in objects:

<%block filter="carriage_returns, tabulation">
    <span class="right">DEPOSIT SLIP ${carrier_name(deposit.carrier_type) or ''}</span>
    N° CLIENT<span class="valign_up">://t${''}</span>
    <span class="right">PRINT ${formatLang(str(date.today()), date=True)}</span>
    ACCOUNT NAME<span class="valign_up">://t${user.company_id.name}</span>
    DOCUMENT N°<span class="valign_up">://t${deposit.name} - ${formatLang(deposit.create_date, date=True)}</span>

</%block>

    <% poids_total = 0 %>
    <% nombre_colis_total = 0 %>
    <table style="border:solid 1px" width="100%">
      <caption></caption>
      <tr align="left">
        <th>Sender Ref</th>
        <th>Name and address<br />destinataire</th>
        <th>Parcel number</th>
        <th class="small">ZIP</th>
        <th class="small">Country</th>
        <th class="small">Weight<br />(KG)</th>
      </tr>
      %for line in deposit.picking_ids:
      <tr align="left">
          <td>${line.name}</td>
          <td>${line.partner_id.name or ''} ${line.partner_id.street or ''}</td>
          <td>${line.carrier_tracking_ref or ''}</td>
          <td>${line.partner_id.zip or ''}</td>
          <td>${line.partner_id.country_id and line.partner_id.country_id.code or ''}</td>
          <td>${line.weight}</td>
      </tr>
        <% poids_total += line.weight %>
        <% nombre_colis_total += 1 %>
      %endfor
    </table>
    <%block filter="carriage_returns, tabulation">
    <div class="bottom_fixed">
        <table>
            <tr>
                <td style="width: 340px;">
    TOTAL PARCEL <span class="valign_bot">://t${nombre_colis_total or '0'}</span>
    TOTAL WEIGHT<span class="valign_bot">://t${poids_total or '0'}</span>
    </div>
            </td>
            <td>
    <p style="width: 240px;" class="cadre_bottom">VISA <br>
      <br>
      DATE
    </p>
            </td>
        </tr>
    </table>
    </%block>
    <p style="page-break-before: always" />

%endfor
</body>
</html>


