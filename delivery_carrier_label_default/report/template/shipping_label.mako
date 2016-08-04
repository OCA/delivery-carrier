<html>
  <head>
  </head>
  <body>
      <%page expression_filter="entity"/>

      <%def name="address(partner, commercial_partner=None)">
          <% company_partner = False %>
          %if commercial_partner:
              %if commercial_partner.id != partner.id:
                  <% company_partner = commercial_partner %>
              %endif
          %elif partner.parent_id:
              <% company_partner = partner.parent_id %>
          %endif

          %if company_partner:
              <tr><td class="name">${company_partner.name or ''}</td></tr>
              <tr><td>${partner.title and partner.title.name or ''} ${partner.name}</td></tr>
              <% address_lines = partner.contact_address.split("\n")[1:] %>
          %else:
              <tr><td class="name">${partner.title and partner.title.name or ''} ${partner.name}</td></tr>
              <% address_lines = partner.contact_address.split("\n") %>
          %endif
          %for part in address_lines:
              %if part:
                  <tr><td>${part}</td></tr>
              %endif
          %endfor
      </%def>

      %for picking in objects:
        <% partner = picking.partner_id %>
        <% setLang(partner.lang) %>
        <div class="address">
          <table class="recipient">
            ${address(partner=partner)}
          </table>
        </div>
      %endfor

  </body>
</html>
