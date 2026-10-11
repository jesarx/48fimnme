# Códigos QR de la página de descargas, generados al compilar el sitio.
#
# Cada QR lleva la dirección completa (url + baseurl de _config.yml) del
# archivo o de la página: si el sitio se publica en otro dominio (el
# definitivo), basta cambiar «url» en _config.yml y volver a compilar
# (sitio/genera.sh --compilar o sitio/publicar.sh) para que los QR apunten ahí.
#
# Genera descargas/qr-<id>.svg para cada archivo de _data/descargas.json y
# descargas/qr-descargas.svg para la propia página de descargas. La página
# los muestra y se pueden descargar para imprimirlos.
#
# Usa la gema rqrcode_core (Ruby puro, sin dependencias; está en el Gemfile:
# cd sitio && bundle install). Sin ella el sitio se compila igual, sin QR.

begin
  require "rqrcode_core"
rescue LoadError
  nil
end

module FIMNME
  module QR
    VERDEOSCURO = "#172B20"
    BORDE = 4   # módulos de margen alrededor (lo que pide la norma)

    # SVG del QR de texto: un solo trazado, con las filas de módulos oscuros
    # unidas para que pese poco
    def self.svg(texto, titulo)
      qr = RQRCodeCore::QRCode.new(texto, level: :m)
      n = qr.modules.size
      lado = n + 2 * BORDE
      trazos = []
      qr.modules.each_with_index do |fila, y|
        x = 0
        while x < n
          if fila[x]
            inicio = x
            x += 1 while x < n && fila[x]
            trazos << "M#{inicio + BORDE} #{y + BORDE}h#{x - inicio}v1h-#{x - inicio}z"
          else
            x += 1
          end
        end
      end
      titulo_xml = titulo.encode(xml: :text)
      <<~SVG
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 #{lado} #{lado}" width="#{lado * 8}" height="#{lado * 8}" shape-rendering="crispEdges" role="img" aria-label="#{titulo_xml}">
        <title>#{titulo_xml}</title>
        <rect width="#{lado}" height="#{lado}" fill="#FFFFFF"/>
        <path fill="#{VERDEOSCURO}" d="#{trazos.join}"/>
        </svg>
      SVG
    end

    class Generador < Jekyll::Generator
      safe true
      priority :low

      def generate(site)
        unless defined?(RQRCodeCore)
          Jekyll.logger.warn "QR:", "falta la gema rqrcode_core (cd sitio && bundle install): la página de descargas sale sin QR."
          return
        end
        base = site.config["url"].to_s.chomp("/") + site.config["baseurl"].to_s
        destinos = (site.data["descargas"] || []).map do |d|
          [d["id"], "#{base}/descargas/#{d['archivo']}", "Código QR para descargar: #{d['titulo']}"]
        end
        destinos << ["descargas", "#{base}/descargas/", "Código QR de la página de descargas"]
        destinos.each do |id, enlace, titulo|
          pagina = Jekyll::PageWithoutAFile.new(site, site.source, "descargas", "qr-#{id}.svg")
          pagina.content = svg(enlace, titulo)
          pagina.data["layout"] = nil
          pagina.data["sitemap"] = false
          site.pages << pagina
        end
        site.config["qr"] = destinos.to_h { |id, enlace, _| [id, enlace] }
      end

      private

      def svg(texto, titulo)
        QR.svg(texto, titulo)
      end
    end
  end
end
