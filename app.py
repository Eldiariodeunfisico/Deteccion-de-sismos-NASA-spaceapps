import streamlit as st
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
from src.data_utils import (load_data, get_list_of_data_training,
                            get_match_filename_training, load_special_file, plot_values_from_special_content,
                            apply_bandpass_filter, apply_highpass_filter, apply_lst_sta_algo_and_plot_char_func,
                            calculate_on_off_cft_and_plot, plot_real_trigger_axvline, calculate_arrival_time, 
                            calculate_predicted_arrival_time, calculate_root_mean_square_error,
                            get_list_of_data_testing, apply_hilbert_and_plot_char, apply_find_peaks_of_energy_amplitude_function)

def training_data_visualization_review():
    import streamlit as st

    folder_selection = st.selectbox(label="Select what data you want to see", options=["mars", "lunar"])

    list_data_df = get_list_of_data_training(folder_selection, "csv")

    # Configure grid options using GridOptionsBuilder
    list_data_df_builder = GridOptionsBuilder.from_dataframe(list_data_df)
    list_data_df_builder.configure_pagination(enabled=True)
    list_data_df_builder.configure_selection(selection_mode='single', use_checkbox=False)
    grid_options = list_data_df_builder.build()

    # Display AgGrid
    st.write("List of Data for Mars/Lunar")
    list_data_df_return_value = AgGrid(list_data_df, gridOptions=grid_options)

    if list_data_df_return_value["selected_data"] is not None:
        selected_value = list_data_df_return_value["selected_data"]["path"].values[0]
        selected_df = load_data(selected_value)
        extension = "mseed"
        match_filename = get_match_filename_training(selected_df["filename"].to_list(), folder_selection, extension)

        st.write(f"List of Data for selected value: {selected_value}")

        # Configure grid options using GridOptionsBuilder
        selected_df_builder = GridOptionsBuilder.from_dataframe(selected_df)
        selected_df_builder.configure_pagination(enabled=True)
        selected_df_builder.configure_selection(selection_mode='single', use_checkbox=False)
        grid_options = selected_df_builder.build()
        selected_df_return_value = AgGrid(selected_df, gridOptions=grid_options)

        # Plot current data
        if selected_df_return_value["selected_data"] is not None:
            selected_value = selected_df_return_value["selected_data"]["filename"].values[0]
            selected_arrival_time = selected_df_return_value["selected_data"]["time_abs(%Y-%m-%dT%H:%M:%S.%f)"].values[0]
            selected_arrival_time = datetime.strptime(selected_arrival_time, '%Y-%m-%dT%H:%M:%S.%f')
            st.write(f"Plot of the time series for file {selected_value}")
            file_name_to_analyze = match_filename[selected_value]
            selected_sample_st = load_special_file(file_name_to_analyze)
            fig, ax = plot_values_from_special_content(selected_sample_st, file_name_to_analyze, selected_arrival_time, plot_real=True)
            st.pyplot(fig, clear_figure=False)

            # Set Up filters
            st.write("High Pass Configuration")
            left, right = st.columns(2)
            freq_input = left.text_input(label="freq", value="2")
            corners_input = right.text_input(label="corners", value="4")
            st.write("Band Pass Configuration")
            left, right = st.columns(2)
            min_freq = left.text_input(label="min_freq", value="0.4")
            max_freq = right.text_input(label="max_freq", value="1.0")
            last_data_st, cft = None, None

            left, middle, right = st.columns(3)

            if left.button("apply highpass", use_container_width=True):
                hp_st_data = apply_highpass_filter(selected_sample_st, float(freq_input), int(corners_input))
                fig, _ = plot_values_from_special_content(hp_st_data, file_name_to_analyze, selected_arrival_time, "High Pass Filter", plot_real=True, plot_spectogram=True)
                st.session_state["fig"] = fig
                st.session_state["last_data_st"] = hp_st_data.copy()

            if middle.button("apply bandpass", use_container_width=True):
                bp_st_data = apply_bandpass_filter(selected_sample_st, float(min_freq), float(max_freq))
                fig, _ = plot_values_from_special_content(bp_st_data, file_name_to_analyze, selected_arrival_time, "Band Pass Filter", plot_real=True, plot_spectogram=True)
                st.session_state["fig"] = fig
                st.session_state["last_data_st"] = bp_st_data.copy()

            if right.button("hp + bp", use_container_width=True):
                hp_st_data = apply_highpass_filter(selected_sample_st, float(freq_input), int(corners_input))
                bp_st_data = apply_bandpass_filter(hp_st_data, float(min_freq), float(max_freq))
                fig, _ = plot_values_from_special_content(bp_st_data, file_name_to_analyze, selected_arrival_time, "HP + BP Filter", plot_real=True, plot_spectogram=True)
                st.session_state["fig"] = fig
                st.session_state["last_data_st"] = bp_st_data.copy()

            if st.session_state.get("fig"):
                st.pyplot(st.session_state.get("fig"), clear_figure=False)

                # Apply algorithm STA/LTA
                st.write("STA/LTA Configuration")
                left, right = st.columns(2)
                sta_len = left.text_input(label="sta len", value="120")
                lta_len = right.text_input(label="lta len", value="600")
                if st.button("Apply STA/LTA", use_container_width=True):
                    if st.session_state.get("last_data_st") is not None:
                        cft, fig, ax = apply_lst_sta_algo_and_plot_char_func(st.session_state.get("last_data_st"),
                                                                             float(sta_len), float(lta_len))
                        st.session_state["cft"] = cft
                        st.session_state["fig_cft"] = fig

                if st.session_state.get("fig_cft"):
                    st.pyplot(st.session_state.get("fig_cft"), clear_figure=False)

                    st.write("On/Off points configuration")
                    left, right = st.columns(2)
                    trh_on = left.text_input(label="thr on", value="4")
                    trh_off = right.text_input(label="thr off", value="1.5")
                    if st.button("Calculate On/Off points", use_container_width=True):
                        if st.session_state.get("cft") is not None:
                            triggers, fig, ax = calculate_on_off_cft_and_plot(st.session_state.get("last_data_st"),
                                                                              st.session_state.get("cft"),
                                                                              float(trh_on), float(trh_off))
                            fig, ax = plot_real_trigger_axvline(st.session_state.get("last_data_st"), selected_arrival_time, ax, fig)

                            if not triggers:
                                st.warning("Method could not detect the triggers change parameters")

                            st.session_state["triggers"] = triggers
                            st.pyplot(fig, clear_figure=False)
                            if triggers:
                                st.write("Error between the actual arrival time and detection")
                                left, right = st.columns(2)
                                real_arrival_time = calculate_arrival_time(st.session_state.get('last_data_st'), selected_arrival_time)
                                predicted_arrival_time = calculate_predicted_arrival_time(st.session_state.get('last_data_st'), triggers)
                                left.write(f"Actual: {real_arrival_time}")
                                right.write(f"Detected: {predicted_arrival_time}")
                                st.write(f"MSE: {calculate_root_mean_square_error(predicted_arrival_time, real_arrival_time)}")


def testing_data_visualization_review():
    import streamlit as st

    folder_selection = st.selectbox(label="Select what test data you want to see", options=["mars", "lunar"])

    list_data_df = get_list_of_data_testing(folder_selection, "mseed")

    # Configure grid options using GridOptionsBuilder
    list_data_df_builder = GridOptionsBuilder.from_dataframe(list_data_df)
    list_data_df_builder.configure_pagination(enabled=True)
    list_data_df_builder.configure_selection(selection_mode='single', use_checkbox=False)
    grid_options = list_data_df_builder.build()

    # Display AgGrid
    st.write("List of Data for Mars/Lunar")
    list_data_df_return_value = AgGrid(list_data_df, gridOptions=grid_options)

    if list_data_df_return_value["selected_data"] is not None:
        selected_value = list_data_df_return_value["selected_data"]["path"].values[0]
        file_name_to_analyze = selected_value

        # Plot current data
        st.write(f"Plot of the time series for file {selected_value}")
        selected_sample_st = load_special_file(file_name_to_analyze)
        fig, ax = plot_values_from_special_content(selected_sample_st, file_name_to_analyze)
        st.pyplot(fig, clear_figure=False)

        # Set Up filters
        st.write("High Pass Configuration")
        left, right = st.columns(2)
        freq_input = left.text_input(label="freq", value="2")
        corners_input = right.text_input(label="corners", value="4")
        st.write("Band Pass Configuration")
        left, right = st.columns(2)
        min_freq = left.text_input(label="min_freq", value="0.4")
        max_freq = right.text_input(label="max_freq", value="1.0")
        last_data_st, cft = None, None

        left, middle, right = st.columns(3)

        if left.button("apply highpass", use_container_width=True):
            hp_st_data = apply_highpass_filter(selected_sample_st, float(freq_input), int(corners_input))
            fig, _ = plot_values_from_special_content(hp_st_data, file_name_to_analyze, title="High Pass Filter", plot_spectogram=True)
            st.session_state["fig_test"] = fig
            st.session_state["last_data_st_test"] = hp_st_data.copy()

        if middle.button("apply bandpass", use_container_width=True):
            bp_st_data = apply_bandpass_filter(selected_sample_st, float(min_freq), float(max_freq))
            fig, _ = plot_values_from_special_content(bp_st_data, file_name_to_analyze, title="Band Pass Filter", plot_spectogram=True)
            st.session_state["fig_test"] = fig
            st.session_state["last_data_st_test"] = bp_st_data.copy()

        if right.button("hp + bp", use_container_width=True):
            hp_st_data = apply_highpass_filter(selected_sample_st, float(freq_input), int(corners_input))
            bp_st_data = apply_bandpass_filter(hp_st_data, float(min_freq), float(max_freq))
            fig, _ = plot_values_from_special_content(bp_st_data, file_name_to_analyze, title="HP + BP Filter", plot_spectogram=True)
            st.session_state["fig_test"] = fig
            st.session_state["last_data_st_test"] = bp_st_data.copy()

        if st.session_state.get("fig_test"):
            st.pyplot(st.session_state.get("fig_test"), clear_figure=False)

            # Apply algorithm STA/LTA
            st.write("STA/LTA Configuration")
            left, right = st.columns(2)
            sta_len = left.text_input(label="sta len", value="120")
            lta_len = right.text_input(label="lta len", value="600")
            if st.button("Apply STA/LTA", use_container_width=True):
                if st.session_state.get("last_data_st_test") is not None:
                    cft, fig, ax = apply_lst_sta_algo_and_plot_char_func(st.session_state.get("last_data_st_test"),
                                                                         float(sta_len), float(lta_len))
                    st.session_state["cft_test"] = cft
                    st.session_state["fig_cft_test"] = fig

            if st.session_state.get("fig_cft_test"):
                st.pyplot(st.session_state.get("fig_cft_test"), clear_figure=False)

                st.write("On/Off points configuration")
                left, right = st.columns(2)
                trh_on = left.text_input(label="thr on", value="4")
                trh_off = right.text_input(label="thr off", value="1.5")
                if st.button("Calculate On/Off points", use_container_width=True):
                    if st.session_state.get("cft_test") is not None:
                        triggers, fig, ax = calculate_on_off_cft_and_plot(st.session_state.get("last_data_st_test"),
                                                                          st.session_state.get("cft_test"),
                                                                          float(trh_on), float(trh_off))

                        if not triggers:
                            st.warning("Method could not detect the triggers change parameters")

                        st.session_state["triggers_test"] = triggers
                        st.pyplot(fig, clear_figure=False)
                        if triggers:
                            st.write("Detection")
                            predicted_arrival_time = calculate_predicted_arrival_time(st.session_state.get('last_data_st_test'), triggers)
                            st.write(f"Detected: {predicted_arrival_time}")

def training_data_visualization_energy_peak_review():
    import streamlit as st

    folder_selection = st.selectbox(label="Select what data you want to see", options=["mars", "lunar"])

    list_data_df = get_list_of_data_training(folder_selection, "csv")

    # Configure grid options using GridOptionsBuilder
    list_data_df_builder = GridOptionsBuilder.from_dataframe(list_data_df)
    list_data_df_builder.configure_pagination(enabled=True)
    list_data_df_builder.configure_selection(selection_mode='single', use_checkbox=False)
    grid_options = list_data_df_builder.build()

    # Display AgGrid
    st.write("List of Data for Mars/Lunar")
    list_data_df_return_value = AgGrid(list_data_df, gridOptions=grid_options)

    if list_data_df_return_value["selected_data"] is not None:
        selected_value = list_data_df_return_value["selected_data"]["path"].values[0]
        selected_df = load_data(selected_value)
        extension = "mseed"
        match_filename = get_match_filename_training(selected_df["filename"].to_list(), folder_selection, extension)

        st.write(f"List of Data for selected value: {selected_value}")

        # Configure grid options using GridOptionsBuilder
        selected_df_builder = GridOptionsBuilder.from_dataframe(selected_df)
        selected_df_builder.configure_pagination(enabled=True)
        selected_df_builder.configure_selection(selection_mode='single', use_checkbox=False)
        grid_options = selected_df_builder.build()
        selected_df_return_value = AgGrid(selected_df, gridOptions=grid_options)

        # Plot current data
        if selected_df_return_value["selected_data"] is not None:
            selected_value = selected_df_return_value["selected_data"]["filename"].values[0]
            selected_arrival_time = selected_df_return_value["selected_data"]["time_abs(%Y-%m-%dT%H:%M:%S.%f)"].values[0]
            selected_arrival_time = datetime.strptime(selected_arrival_time, '%Y-%m-%dT%H:%M:%S.%f')
            st.write(f"Plot of the time series for file {selected_value}")
            file_name_to_analyze = match_filename[selected_value]
            selected_sample_st = load_special_file(file_name_to_analyze)
            fig, ax = plot_values_from_special_content(selected_sample_st, file_name_to_analyze, selected_arrival_time, plot_real=True)
            st.pyplot(fig, clear_figure=False)

            # Set Up filters
            st.write("High Pass Configuration")
            left, right = st.columns(2)
            freq_input = left.text_input(label="freq", value="3")
            corners_input = right.text_input(label="corners", value="4")
            st.write("Band Pass Configuration")
            left, right = st.columns(2)
            min_freq = left.text_input(label="min_freq", value="0.5")
            max_freq = right.text_input(label="max_freq", value="1.0")
            last_data_st, cft = None, None

            left, middle, right = st.columns(3)

            if left.button("apply highpass", use_container_width=True):
                hp_st_data = apply_highpass_filter(selected_sample_st, float(freq_input), int(corners_input))
                fig, _ = plot_values_from_special_content(hp_st_data, file_name_to_analyze, selected_arrival_time, "High Pass Filter", plot_real=True, plot_spectogram=True)
                st.session_state["fig_peak_energy"] = fig
                st.session_state["last_data_st_peak_energy"] = hp_st_data.copy()

            if middle.button("apply bandpass", use_container_width=True):
                bp_st_data = apply_bandpass_filter(selected_sample_st, float(min_freq), float(max_freq))
                fig, _ = plot_values_from_special_content(bp_st_data, file_name_to_analyze, selected_arrival_time, "Band Pass Filter", plot_real=True, plot_spectogram=True)
                st.session_state["fig_peak_energy"] = fig
                st.session_state["last_data_st_peak_energy"] = bp_st_data.copy()

            if right.button("hp + bp", use_container_width=True):
                hp_st_data = apply_highpass_filter(selected_sample_st, float(freq_input), int(corners_input))
                bp_st_data = apply_bandpass_filter(hp_st_data, float(min_freq), float(max_freq))
                fig, _ = plot_values_from_special_content(bp_st_data, file_name_to_analyze, selected_arrival_time, "HP + BP Filter", plot_real=True, plot_spectogram=True)
                st.session_state["fig_peak_energy"] = fig
                st.session_state["last_data_st_peak_energy"] = bp_st_data.copy()

            if st.session_state.get("fig_peak_energy"):
                st.pyplot(st.session_state.get("fig_peak_energy"), clear_figure=False)
                # Apply algorithm
                st.write("Amplitude detection")
                if st.button("Apply hilbert transform to our signal", use_container_width=True):
                    if st.session_state.get("last_data_st_peak_energy") is not None:
                        amplitude, fig, ax = apply_hilbert_and_plot_char(st.session_state.get("last_data_st_peak_energy"),
                                                                         file_name_to_analyze,
                                                                         selected_arrival_time, plot_real=True)
                        st.session_state["amplitude_peak"] = amplitude
                        st.session_state["fig_amplitude"] = fig

                if st.session_state.get("fig_amplitude"):
                    st.pyplot(st.session_state.get("fig_amplitude"), clear_figure=False)
                    st.write("Get Peaks Configuration")
                    left, right = st.columns(2)
                    min_distance = left.text_input(label="min distance", value="40000")
                    percentile_thr = right.text_input(label="percentile thr", value="99.5")
                    if st.button("Calculate peak points", use_container_width=True):
                        if st.session_state.get("amplitude_peak") is not None:
                            peaks, fig, ax = apply_find_peaks_of_energy_amplitude_function(
                                st.session_state.get("last_data_st_peak_energy"),
                                st.session_state.get("amplitude_peak"),
                                min_distance=float(min_distance),
                                percentile_value=float(percentile_thr),
                                arrival_time=selected_arrival_time, 
                                plot_real=True,
                                file_name_to_analyze=file_name_to_analyze)

                            if peaks is None and len(peaks) <= 0:
                                st.warning("Method could not detect the triggers change parameters")

                            st.session_state["peaks"] = peaks
                            st.pyplot(fig, clear_figure=False)
                            
                            if peaks is not None and len(peaks) > 0:
                                st.write("Error between the actual arrival time and detection")
                                left, right = st.columns(2)
                                real_arrival_time = calculate_arrival_time(st.session_state.get('last_data_st_peak_energy'), selected_arrival_time)
                                predicted_arrival_time = calculate_predicted_arrival_time(st.session_state.get('last_data_st_peak_energy'), peaks)
                                left.write(f"Actual: {real_arrival_time}")
                                right.write(f"Detected: {predicted_arrival_time}")
                                st.write(f"MSE: {calculate_root_mean_square_error(predicted_arrival_time, real_arrival_time)}")

def testing_data_visualization_energy_peak_review():
    import streamlit as st
    folder_selection = st.selectbox(label="Select what test data you want to see", options=["mars", "lunar"])

    list_data_df = get_list_of_data_testing(folder_selection, "mseed")

    # Configure grid options using GridOptionsBuilder
    list_data_df_builder = GridOptionsBuilder.from_dataframe(list_data_df)
    list_data_df_builder.configure_pagination(enabled=True)
    list_data_df_builder.configure_selection(selection_mode='single', use_checkbox=False)
    grid_options = list_data_df_builder.build()

    # Display AgGrid
    st.write("List of Data for Mars/Lunar")
    list_data_df_return_value = AgGrid(list_data_df, gridOptions=grid_options)

    if list_data_df_return_value["selected_data"] is not None:
        selected_value = list_data_df_return_value["selected_data"]["path"].values[0]
        file_name_to_analyze = selected_value

        # Plot current data
        st.write(f"Plot of the time series for file {selected_value}")
        selected_sample_st = load_special_file(file_name_to_analyze)
        fig, ax = plot_values_from_special_content(selected_sample_st, file_name_to_analyze)
        st.pyplot(fig, clear_figure=False)

        # Set Up filters
        st.write("High Pass Configuration")
        left, right = st.columns(2)
        freq_input = left.text_input(label="freq", value="3")
        corners_input = right.text_input(label="corners", value="4")
        st.write("Band Pass Configuration")
        left, right = st.columns(2)
        min_freq = left.text_input(label="min_freq", value="0.5")
        max_freq = right.text_input(label="max_freq", value="1.0")
        last_data_st, cft = None, None

        left, middle, right = st.columns(3)

        if left.button("apply highpass", use_container_width=True):
            hp_st_data = apply_highpass_filter(selected_sample_st, float(freq_input), int(corners_input))
            fig, _ = plot_values_from_special_content(hp_st_data, file_name_to_analyze, title="High Pass Filter", plot_spectogram=True)
            st.session_state["fig_peak_test"] = fig
            st.session_state["last_data_st_peak_test"] = hp_st_data.copy()

        if middle.button("apply bandpass", use_container_width=True):
            bp_st_data = apply_bandpass_filter(selected_sample_st, float(min_freq), float(max_freq))
            fig, _ = plot_values_from_special_content(bp_st_data, file_name_to_analyze, title="Band Pass Filter", plot_spectogram=True)
            st.session_state["fig_peak_test"] = fig
            st.session_state["last_data_st_peak_test"] = bp_st_data.copy()

        if right.button("hp + bp", use_container_width=True):
            hp_st_data = apply_highpass_filter(selected_sample_st, float(freq_input), int(corners_input))
            bp_st_data = apply_bandpass_filter(hp_st_data, float(min_freq), float(max_freq))
            fig, _ = plot_values_from_special_content(bp_st_data, file_name_to_analyze, title="HP + BP Filter", plot_spectogram=True)
            st.session_state["fig_peak_test"] = fig
            st.session_state["last_data_st_peak_test"] = bp_st_data.copy()

        if st.session_state.get("fig_peak_test"):
            st.pyplot(st.session_state.get("fig_peak_test"), clear_figure=False)

            # Apply algorithm
            st.write("Amplitude detection")
            if st.button("Apply hilbert transform to our signal", use_container_width=True):
                if st.session_state.get("last_data_st_peak_test") is not None:
                    amplitude, fig, ax = apply_hilbert_and_plot_char(st.session_state.get("last_data_st_peak_test"),
                                                                     file_name_to_analyze)
                    st.session_state["amplitude_peak_test"] = amplitude
                    st.session_state["fig_amplitude_test"] = fig

            if st.session_state.get("fig_amplitude_test"):
                st.pyplot(st.session_state.get("fig_amplitude_test"), clear_figure=False)

                st.write("Get Peaks Configuration")
                left, right = st.columns(2)
                min_distance = left.text_input(label="min distance", value="40000")
                percentile_thr = right.text_input(label="percentile thr", value="99.5")
                if st.button("Calculate peak points", use_container_width=True):
                    if st.session_state.get("amplitude_peak_test") is not None:
                        peaks, fig, ax = apply_find_peaks_of_energy_amplitude_function(
                            st.session_state.get("last_data_st_peak_test"),
                            st.session_state.get("amplitude_peak_test"),
                            min_distance=float(min_distance),
                            percentile_value=float(percentile_thr),
                            file_name_to_analyze=file_name_to_analyze)

                        if peaks is None and len(peaks) <= 0:
                            st.warning("Method could not detect the triggers change parameters")

                        st.session_state["peaks_test"] = peaks
                        st.pyplot(fig, clear_figure=False)

                        if peaks is not None and len(peaks) > 0:
                            st.write("Error between the actual arrival time and detection")
                            predicted_arrival_time = calculate_predicted_arrival_time(st.session_state.get('last_data_st_peak_test'), peaks)
                            st.write(f"Detected: {predicted_arrival_time}")

page_names_to_funcs = {
    "train sta/dta interactive visualization": training_data_visualization_review,
    "test sta/dta interactive visualization": testing_data_visualization_review,
    "train energy peak interactive visualization": training_data_visualization_energy_peak_review,
    "test energy peak interactive visualization": testing_data_visualization_energy_peak_review
}

demo_name = st.sidebar.selectbox("Choose what you want to see", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()