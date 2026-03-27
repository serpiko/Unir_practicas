#!/usr/bin/env python3
"""
    Trabajo práctico para la asignatura de
    Tecnologías Emergentes en el curso de adaptación al grado Unir
    Año 2025/26
    Alumno: Raúl Muñoz

    Análisis de recorrido de rutas GPX
    comparativa de recorrido pre-diseñado ( teórico ) para una
    ruta en bicicleta ( o a pie ) con el práctico, cuando se
    realiza la ruta en tiempo real, registrando los puntos
    geográficos ( waypoints )

    uso de distancia de Haversine para puntos geográficos en una
    esfera como la Tierra.
"""

import argparse
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from matplotlib import gridspec
from matplotlib import pyplot as plt

# GPX namespace
NS = {"gpx": "http://www.topografix.com/GPX/1/1"}


@dataclass
class Point:
    lat: float
    lon: float
    ele: float | None
    time: datetime | None


@dataclass
class SpeedData:
    times: list
    duration: float
    avg_speed_kmh: float
    speeds: np.ndarray
    stopped_pct: float
    cum_r: list[float]


def parse_gpx(path: str) -> list[Point]:
    """Devuelve lista de puntos extraidos del fichero GPX"""
    tree = ET.parse(path)
    root = tree.getroot()
    points = []
    for trkpt in root.findall(".//gpx:trkpt", NS):
        ele_el = trkpt.find("gpx:ele", NS)
        time_el = trkpt.find("gpx:time", NS)
        points.append(
            Point(
                lat=float(trkpt.attrib["lat"]),
                lon=float(trkpt.attrib["lon"]),
                ele=float(ele_el.text) if ele_el is not None else None,
                time=datetime.fromisoformat(time_el.text)
                if time_el is not None else None,
            )
        )
    return points


def haversine(a: Point, b: Point) -> float:
    """Distancia entre 2 puntos geograficos.
       denota phi para latitud y lambda para longitud
    """
    EARTH_RADIUS = 6_371_000
    phi1, phi2 = math.radians(a.lat), math.radians(b.lat)
    dphi = math.radians(b.lat - a.lat)
    dlam = math.radians(b.lon - a.lon)
    x = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(x))


def total_distance(points: list[Point]) -> tuple[list[float], float]:
    """distancia acumulada y total"""
    cum = [0.0]
    for i in range(1, len(points)):
        d = haversine(points[i - 1], points[i])
        cum.append(cum[-1] + d)
    return cum, cum[-1]


def assign_buckets(
    real: list[Point], cum_r: list[float], dist_r: float,
    teorica: list[Point], cum_t: list[float], dist_t: float,
) -> list[int]:
    """
    Para cada punto real, calcula qué índice teórico le corresponde
    usando la fracción de distancia acumulada recorrida.
    Ej: si en el punto real1  llevas el 40% distancia real,
    lo asignamos al punto teórico +cerca al 40% de distancia teórica.
    """
    buckets = []
    for i in range(len(real)):
        fraccion = cum_r[i] / dist_r
        d_teorica = fraccion * dist_t
        # índice teórico cuya distancia acumulada está más cerca de d_teorica
        idx = min(range(len(cum_t)), key=lambda j: abs(cum_t[j] - d_teorica))
        buckets.append(idx)
    return buckets


def elevation_gain_loss(points: list[Point]) -> tuple[float, float]:
    """calculamos elevación acumulada: positiva, negativa"""
    ele = np.array([p.ele for p in points if p.ele is not None], dtype=float)
    diff = np.diff(ele)
    return float(diff[diff > 0].sum()), float(abs(diff[diff < 0].sum()))


def print_route_summary(
    teorica: list[Point], real: list[Point], dist_t: float, dist_r: float
) -> None:
    """Imprime cabecera y comparativa de distancias"""
    print("=" * 60)
    print("  INFORME DE COMPARACIÓN DE RUTAS GPX")
    print("=" * 60)
    print(f"\nRuta teórica   (ruta_teorica):  {len(teorica):>5} puntos  |  {dist_t / 1000:.3f} km")
    print(f"Recorrido real (Samsung Health): {len(real):>5} puntos  |  {dist_r / 1000:.3f} km")
    print(
        f"Diferencia de distancia: {abs(dist_r - dist_t) / 1000:.3f} km  "
        f"({(dist_r - dist_t) / dist_t * 100:+.1f}%)"
    )


def print_deviation_stats(dev: np.ndarray, label: str) -> None:
    """Imprime estadísticas de desviación"""
    print(f"\n{'─' * 60}")
    print(f"  DESVIACIÓN — {label}")
    print(f"{'─' * 60}")
    print(f"  Puntos analizados:     {len(dev)}")
    print(f"  Desviación media:      {dev.mean():.1f} m")
    print(f"  Desviación mediana:    {np.median(dev):.1f} m")
    print(f"  Desviación típica:     {dev.std():.1f} m")
    print(f"  Desviación máxima:     {dev.max():.1f} m")
    print(f"  Percentil 95:          {np.percentile(dev, 95):.1f} m")
    for threshold in (10, 20, 50, 100):
        pct = (dev <= threshold).mean() * 100
        print(f"  Dentro de {threshold:>3} m:        {pct:.1f}%")


def compute_elevation(
    teorica: list[Point], real: list[Point]
) -> tuple[list, list, float, float, float, float]:
    """Extrae listas de elevación y calcula desniveles"""
    ele_t = [p.ele for p in teorica if p.ele is not None]
    ele_r = [p.ele for p in real if p.ele is not None]
    gain_t, loss_t = elevation_gain_loss(teorica)
    gain_r, loss_r = elevation_gain_loss(real)
    return ele_t, ele_r, gain_t, loss_t, gain_r, loss_r


def print_elevation_stats(
    ele_t: list, ele_r: list, gain_t: float, loss_t: float, gain_r: float, loss_r: float
) -> None:
    """Imprime estadísticas de elevación"""
    print(f"\n{'─' * 60}")
    print("  ELEVACIÓN")
    print(f"{'─' * 60}")
    print(
        f"  Teórica: min {min(ele_t):.1f} m  max {max(ele_t):.1f} m  "
        f"subida +{gain_t:.0f} m  bajada -{loss_t:.0f} m"
    )
    print(
        f"  Real:    min {min(ele_r):.1f} m  max {max(ele_r):.1f} m  "
        f"subida +{gain_r:.0f} m  bajada -{loss_r:.0f} m"
    )


def compute_speed_data(
    real: list[Point], dist_r: float, cum_r: list[float]
) -> SpeedData | None:
    """Calcula estadísticas de velocidad. Devuelve None si no hay datos de tiempo."""
    times = [p.time for p in real if p.time is not None]
    if not times:
        return None

    duration = (times[-1] - times[0]).total_seconds()
    avg_speed_kmh = (dist_r / 1000) / (duration / 3600)

    speeds = []
    for i in range(1, len(real)):
        if real[i].time and real[i - 1].time:
            dt = (real[i].time - real[i - 1].time).total_seconds()
            if dt > 0:
                d = haversine(real[i - 1], real[i])
                speeds.append((d / dt) * 3.6)  # km/h
    speeds = np.array(speeds)

    return SpeedData(
        times=times,
        duration=duration,
        avg_speed_kmh=avg_speed_kmh,
        speeds=speeds,
        stopped_pct=(speeds < 1.0).mean() * 100,
        cum_r=cum_r,
    )


def print_speed_stats(sd: SpeedData) -> None:
    """Imprime estadísticas de tiempo y velocidad"""
    print(f"\n{'─' * 60}")
    print("  TIEMPO Y VELOCIDAD DEL RECORRIDO REAL")
    print(f"{'─' * 60}")
    start_local = sd.times[0].astimezone()
    end_local = sd.times[-1].astimezone()
    print(f"  Inicio:            {start_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Fin:               {end_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    h, rem = divmod(int(sd.duration), 3600)
    m, s = divmod(rem, 60)
    print(f"  Duración:          {h:02d}:{m:02d}:{s:02d}")
    print(f"  Velocidad media:   {sd.avg_speed_kmh:.1f} km/h")
    print(f"  Velocidad máxima:  {sd.speeds.max():.1f} km/h")
    print(f"  Velocidad mediana: {np.median(sd.speeds):.1f} km/h")
    print(f"  Parado (<1 km/h):  {sd.stopped_pct:.1f}% de los intervalos")


def build_plots(
    teorica: list[Point],
    real: list[Point],
    cum_t: list[float],
    cum_r: list[float],
    dev: np.ndarray,
    ele_t: list,
    ele_r: list,
    sd: SpeedData | None,
) -> None:
    """Genera y guarda las gráficas de comparación"""
    lat_t = [p.lat for p in teorica]
    lon_t = [p.lon for p in teorica]
    lat_r = [p.lat for p in real]
    lon_r = [p.lon for p in real]

    fig = plt.figure(figsize=(16, 14))
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.35)

    # 1. mapa
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(lon_t, lat_t, "b-", lw=1.5, alpha=0.7, label="Ruta teórica")
    sc = ax1.scatter(
        lon_r, lat_r,
        c=dev, cmap="RdYlGn_r", s=4, alpha=0.8,
        vmin=0, vmax=min(100, np.percentile(dev, 98)),
        label="Recorrido real (color = desviación)",
    )
    ax1.plot(lon_t[0], lat_t[0], "bs", ms=8, label="Inicio teórico")
    ax1.plot(lon_r[0], lat_r[0], "g^", ms=8, label="Inicio real")
    ax1.plot(lon_r[-1], lat_r[-1], "rv", ms=8, label="Fin real")
    plt.colorbar(sc, ax=ax1, label="Desviación respecto a la teórica (m)")
    ax1.set_xlabel("Longitud")
    ax1.set_ylabel("Latitud")
    ax1.set_title("Mapa de rutas: Teórica vs Real (color = desviación respecto al plan)")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.set_aspect("equal")

    # 2. desviación
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(np.array(cum_r) / 1000, dev, color="coral", lw=0.8, alpha=0.9)
    ax2.fill_between(np.array(cum_r) / 1000, dev, alpha=0.3, color="coral")
    ax2.axhline(dev.mean(), color="red", ls="--", lw=1.2, label=f"Media {dev.mean():.1f} m")
    ax2.axhline(
        np.median(dev), color="orange", ls="--", lw=1.2,
        label=f"Mediana {np.median(dev):.1f} m"
    )
    ax2.set_xlabel("Distancia real (km)")
    ax2.set_ylabel("Desviación (m)")
    ax2.set_title("Desviación respecto a la ruta teórica vs distancia")
    ax2.legend(fontsize=8)
    ax2.set_ylim(bottom=0)

    # 3. altitud
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(np.array(cum_t) / 1000, ele_t, "b-", lw=1.5, alpha=0.8, label="Teórica")
    ax3.plot(np.array(cum_r) / 1000, ele_r, "g-", lw=1.2, alpha=0.8, label="Real")
    ax3.set_xlabel("Distancia (km)")
    ax3.set_ylabel("Altitud(m)")
    ax3.set_title("Perfiles de altitud ")
    ax3.legend(fontsize=8)

    # 4. velocidad/distancia
    if sd is not None and len(sd.speeds) > 0:
        ax4 = fig.add_subplot(gs[2, 0])
        spd_dist = np.array(sd.cum_r[1: len(sd.speeds) + 1]) / 1000
        window = min(30, len(sd.speeds) // 10 or 1)
        smooth_speeds = np.convolve(sd.speeds, np.ones(window) / window, mode="same")
        ax4.plot(
            spd_dist, smooth_speeds,
            color="steelblue", lw=1.2,
            label=f"Velocidad (suavizada, v={window})",
        )
        ax4.fill_between(spd_dist, smooth_speeds, alpha=0.25, color="steelblue")
        ax4.axhline(
            sd.avg_speed_kmh, color="navy", ls="--", lw=1.2,
            label=f"Media {sd.avg_speed_kmh:.1f} km/h"
        )
        ax4.set_xlabel("Distancia (km)")
        ax4.set_ylabel("Velocidad (km/h)")
        ax4.set_title("Perfil de velocidad (recorrido real)")
        ax4.legend(fontsize=8)
        ax4.set_ylim(bottom=0)

    # 5. histograma de desviación
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.hist(dev, bins=50, color="coral", edgecolor="white", lw=0.4, alpha=0.85)
    for thr, col in [(10, "green"), (20, "orange"), (50, "red")]:
        ax5.axvline(
            thr, color=col, ls="--", lw=1.2,
            label=f"{thr} m ({(dev <= thr).mean() * 100:.0f}%)"
        )
    ax5.set_xlabel("Desviación respecto a la ruta teórica (m)")
    ax5.set_ylabel("Número de puntos GPS")
    ax5.set_title("Distribución de desviaciones")
    ax5.legend(fontsize=8)

    fig.suptitle(
        "Comparación de rutas GPX: Teórica vs Recorrido real", fontsize=14, fontweight="bold"
    )
    plt.savefig("gpx_comparison.png", dpi=150, bbox_inches="tight")
    print(f"\n{'─' * 60}")
    print("  Gráfico guardado → gpx_comparison.png")
    print("=" * 60)


def main():
    """programa principal"""
    parser = argparse.ArgumentParser(
        description="Compara una ruta GPX teórica con el recorrido actual."
    )
    parser.add_argument("theoretical", help="fichero GPX teorico")
    parser.add_argument("actual", help="fichero GPX práctico")
    args = parser.parse_args()

    teorica = parse_gpx(args.theoretical)
    real = parse_gpx(args.actual)

    cum_t, dist_t = total_distance(teorica)
    cum_r, dist_r = total_distance(real)

    print_route_summary(teorica, real, dist_t, dist_r)

    buckets = assign_buckets(real, cum_r, dist_r, teorica, cum_t, dist_t)
    dev = np.array([haversine(real[i], teorica[buckets[i]]) for i in range(len(real))])
    print_deviation_stats(dev, "BUCKETS      (447 puntos, vértice por fracción de distancia)")

    ele_t, ele_r, gain_t, loss_t, gain_r, loss_r = compute_elevation(teorica, real)
    print_elevation_stats(ele_t, ele_r, gain_t, loss_t, gain_r, loss_r)

    sd = compute_speed_data(real, dist_r, cum_r)
    if sd:
        print_speed_stats(sd)

    build_plots(teorica, real, cum_t, cum_r, dev, ele_t, ele_r, sd)


if __name__ == "__main__":
    main()